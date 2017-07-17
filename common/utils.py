# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

import logging
import json
import sys
from django.http import HttpResponse
import six
from six import binary_type, text_type
import time
import itertools

logger = logging.getLogger(__name__)

# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PYPY = True if getattr(sys, 'pypy_version_info', None) else False

if PY3:
    from io import BytesIO

    text_type = str
    binary_type = bytes
else:
    from cStringIO import StringIO as BytesIO

    text_type = unicode
    binary_type = str


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


def check_text_content_type(content_type):
    """
    检查content_type 是否是文本类型
    :param content_type:
    :return:
    """
    content_type = text_type(content_type).lower()
    text_content_type = [
        b'text',
        b'application/json',
        b'application/x-javascript',
        b'application/xml',
        b'application/x-www-form-urlencoded'
    ]
    return any(map(content_type.startswith, text_content_type))


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


__all__ = ['grouper', 'check_text_content_type',
           'json_dumps', 'json_loads', 'http_response_json', 'error_404',
           'datetime_to_timestamp', 'datetime_to_str', 'text_type_dict',
           'utf8', 'BytesIO', 'text_type', 'binary_type', 'PY2', 'PY3', 'PYPY']
