# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

import logging
import json

from django.http import HttpResponse
import six
from six import binary_type, text_type
import time

logger = logging.getLogger(__name__)


def utf8(value):
    """Get the UTF8-encoded version of a value."""
    if not isinstance(value, binary_type) and not isinstance(value, text_type):
        value = binary_type(value)
    if isinstance(value, text_type):
        return value.encode('utf-8')
    else:
        return value


def text_type_dict(dict_data):
    if not isinstance(dict_data, dict):
        raise TypeError

    new_dict = {}
    for k, v in dict_data.items():
        if isinstance(k, binary_type):
            k = k.decode('utf-8')
        if isinstance(v, binary_type):
            v = v.decode('utf-8')

        new_dict[k] = v

    return new_dict


def datetime_to_str(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    将datetime转换成字符串
    :param format_str:
    :param dt:
    :return:
    """
    return dt.strftime(format_str) if dt else ''


def datetime_to_timestamp(dt):
    """
    将 datetime 转换成时间戳，精确到毫秒
    :param dt:
    :return:
    """
    if dt is None:
        return None
    else:
        return time.mktime(dt.timetuple()) * 1e3 + dt.microsecond / 1e3


def error_404(request):
    return HttpResponse("page not found")
    # return render_to_response('404.html')


def http_response_json(dict_data, encoding='utf-8'):
    """
    返回json数据
    :param encoding:
    :param dict_data:
    :return:
    """

    # ensure_ascii=False，用来处理中文
    try:
        if six.PY3:
            # if isinstance(dict_data, binary_type):
            #     dict_data =
            dict_data = text_type_dict(dict_data)
            return HttpResponse(json.dumps(dict_data, ensure_ascii=False),
                                content_type="application/json; charset=utf-8")
        else:
            return HttpResponse(json.dumps(dict_data, encoding=encoding, ensure_ascii=False),
                                content_type="application/json; charset=utf-8")
    except Exception as e:
        logger.error(e)
        # 去掉 ensure_ascii 再试一下
        return HttpResponse(json.dumps(dict_data),
                            content_type="application/json; charset=utf-8")


def json_loads(content, encoding=None):
    if six.PY3:
        return json.loads(s=content.decode('utf-8'), encoding=encoding)
    else:
        return json.loads(s=content, encoding=encoding)


def json_dumps(dict_data, encoding='utf-8', indent=None, sort_keys=False):
    """
    返回json数据
    :param sort_keys:
    :param indent:
    :param encoding:
    :param dict_data:
    :return:
    """

    # ensure_ascii=False，用来处理中文
    try:
        return json.dumps(dict_data, encoding=encoding, ensure_ascii=False, indent=indent, sort_keys=sort_keys)
    except Exception as e:
        logger.error(e)
        # 去掉 ensure_ascii 再试一下
        return json.dumps(dict_data, indent=indent, sort_keys=sort_keys)


# ----------------------------------------------------------
# django bulk_update

import itertools

from django.db import connections, models
from django.db.models.query import QuerySet


def _get_db_type(field, connection):
    if isinstance(field, (models.PositiveSmallIntegerField,
                          models.PositiveIntegerField)):
        # integer CHECK ("points" >= 0)'
        return field.db_type(connection).split(' ', 1)[0]

    res = field.db_type(connection)
    return res


def grouper(iterable, size):
    # http://stackoverflow.com/a/8991553
    it = iter(iterable)
    if size <= 0:
        yield it
        return
    while True:
        chunk = tuple(itertools.islice(it, size))
        if not chunk:
            return
        yield chunk


def bulk_update(objs, meta=None, update_fields=None, exclude_fields=None,
                using='default', batch_size=1000):
    assert batch_size is None or batch_size > 0

    # if we have a QuerySet, avoid loading objects into memory
    if isinstance(objs, QuerySet):
        batch_size = batch_size or objs.count()
    else:
        batch_size = batch_size or len(objs)

    connection = connections[using]
    if meta is None:
        # TODO: account for iterables
        meta = objs[0]._meta

    exclude_fields = exclude_fields or []
    update_fields = update_fields or meta.get_all_field_names()
    fields = [
        f for f in meta.fields
        if ((not isinstance(f, models.AutoField))
            and (f.attname in update_fields))]
    fields = [
        f for f in fields
        if f.attname not in exclude_fields]

    # The case clause template; db-dependent
    # Apparently, mysql's castable types are very limited and have
    # nothing to do with the column types. Still, it handles the uncast
    # types well enough... hopefully.
    # http://dev.mysql.com/doc/refman/5.5/en/cast-functions.html#function_cast
    #
    # Sqlite also gives some trouble with cast, at least for datetime,
    # but is also permissive for uncast values
    vendor = connection.vendor
    use_cast = 'mysql' not in vendor and 'sqlite' not in connection.vendor
    if use_cast:
        case_clause_template = '{column} = CAST(CASE {pkcolumn} {{when}}'
        tail_end_template = ' END AS {type})'
    else:
        case_clause_template = '{column} = (CASE {pkcolumn} {{when}}'
        tail_end_template = ' END)'

    for objs_batch in grouper(objs, batch_size):
        pks = []
        case_clauses = {}
        for obj in objs_batch:
            pks.append(obj.pk)
            for field in fields:
                column = field.column

                # Synopsis: make sure the column-specific 'case'
                # exists and then append the obj-specific values to
                # it in a tricky way (leaving ' {when}' at the end).
                # TODO?: For speed, use a list to be ''-joined later,
                # instead? Or a bytearray.
                # TODO: optimise (getitem+setitem vs. get + setitem)
                try:
                    case_clause = case_clauses[column]
                except KeyError:
                    case_clause = {
                        'sql': case_clause_template.format(
                            column=column, pkcolumn=meta.pk.column),
                        'params': [],
                        'type': _get_db_type(field, connection=connection),
                    }
                    case_clauses[column] = case_clause

                case_clause['sql'] = (
                    case_clause['sql'].format(when="WHEN %s THEN %s {when}")
                )

                case_clause['params'].extend(
                    [obj.pk,
                     field.get_db_prep_value(
                         getattr(obj, field.attname), connection)])

        if pks:
            values = ', '.join(
                v['sql'].format(when=tail_end_template.format(type=v['type']))
                for v in case_clauses.values())
            parameters = [
                param
                for clause in case_clauses.values()
                for param in clause['params']]

            del case_clauses  # ... memory

            pkcolumn = meta.pk.column
            dbtable = meta.db_table
            # Storytime: apparently (at least for mysql and sqlite), if a
            # non-simple parameter is added (e.g. a tuple), it is
            # processed with force_text and, accidentally, manages to
            # be a valid syntax... unless there's only one element.
            # So, to fix this, expand the ' in %s' with the parameters' string
            in_clause_sql = '({})'.format(
                ', '.join(itertools.repeat('%s', len(pks))))
            parameters.extend(pks)

            sql = (
                'UPDATE {dbtable} SET {values} WHERE {pkcolumn} '
                'in {in_clause_sql}'
                    .format(
                    dbtable=dbtable, values=values, pkcolumn=pkcolumn,
                    in_clause_sql=in_clause_sql))
            del values, pks

            logger.debug(sql)
            with connection.cursor() as c:
                c.execute(sql, parameters)


# ----------------------------------------------------------


# Bulk insert/update DB operations for the Django ORM. Useful when
# inserting/updating lots of objects where the bottleneck is overhead
# in talking to the database. Instead of doing this
#
#   for x in seq:
#       o = SomeObject()
#       o.foo = x
#       o.save()
#
# or equivalently this
#
#   for x in seq:
#       SomeObject.objects.create(foo=x)
#
# do this
#
#   l = []
#   for x in seq:
#       o = SomeObject()
#       o.foo = x
#       l.append(o)
#   insert_many(l)
#
# Note that these operations are really simple. They won't work with
# many-to-many relationships, and you may have to divide really big
# lists into smaller chunks before sending them through.
#
# History
# 2010-12-10: quote column names, reported by Beres Botond.

def insert_many(objects, using="default", batch_size=2000):
    """Insert list of Django objects in one SQL query. Objects must be
    of the same Django model. Note that save is not called and signals
    on the model are not raised."""

    def batch_insert(objects_batch):
        if not objects_batch:
            return

        import django.db.models
        from django.db import connections

        con = connections[using]

        model = objects_batch[0].__class__
        fields = [f for f in model._meta.fields if not isinstance(f, django.db.models.AutoField)]
        parameters = []
        for o in objects_batch:
            parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields))

        table = model._meta.db_table
        column_names = ",".join(con.ops.quote_name(f.column) for f in fields)
        placeholders = ",".join(("%s",) * len(fields))

        with con.cursor() as c:
            c.executemany(
                "insert into %s (%s) values (%s)" % (table, column_names, placeholders),
                parameters)

    for objs_batch in grouper(objects, batch_size):
        batch_insert(objs_batch)


def update_many(objects, fields=None, using="default"):
    """Update list of Django objects in one SQL query, optionally only
    overwrite the given fields (as names, e.g. fields=["foo"]).
    Objects must be of the same Django model. Note that save is not
    called and signals on the model are not raised."""
    if not objects:
        return

    import django.db.models
    from django.db import connections

    con = connections[using]

    if fields is None:
        fields = []

    names = fields
    meta = objects[0]._meta
    fields = [f for f in meta.fields if
              not isinstance(f, django.db.models.AutoField) and (not names or f.name in names)]

    if not fields:
        raise ValueError("No fields to update, field names are %s." % names)

    fields_with_pk = fields + [meta.pk]
    parameters = []
    for o in objects:
        parameters.append(tuple(f.get_db_prep_save(f.pre_save(o, True), connection=con) for f in fields_with_pk))

    table = meta.db_table
    assignments = ",".join(("%s=%%s" % con.ops.quote_name(f.column)) for f in fields)

    with con.cursor() as c:
        c.executemany(
            "update %s set %s where %s=%%s" % (table, assignments, con.ops.quote_name(meta.pk.column)),
            parameters)
