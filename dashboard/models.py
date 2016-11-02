# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2


from __future__ import unicode_literals, absolute_import
from datetime import datetime, timedelta
from future.moves.urllib.parse import urlparse
from common.utils import text_type, BytesIO, utf8
from bson import ObjectId
from base64 import b64decode
from django.db import models
import gridfs
from django.core.validators import RegexValidator
import hashlib
from api_dashboard.settings import DEFAULT_ASYNC_HTTP_CONNECT_TIMEOUT, \
    DEFAULT_ASYNC_HTTP_REQUEST_TIMEOUT, DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS, \
    DEFAULT_REFRESH_TOKEN_EXPIRE_SECONDS
from common.utils import datetime_to_str, datetime_to_timestamp
from api_dashboard.settings import DEFAULT_ACCESS_LOG_PAGE_SIZE
from mongoengine import *
from mongoengine.connection import get_db
import logging
from .utils import check_text_content_type

logger = logging.getLogger(__name__)


class Client(models.Model):
    """访问请求的客户端"""

    # client 的名称
    name = models.CharField(unique=True, max_length=128)
    # client 的标识，client 发起请求时，使用 access_key 来标识自己，而不是 name
    access_key = models.CharField(unique=True, max_length=128,
                                  validators=[RegexValidator(regex=r'^[_0-9a-zA-Z]+$',
                                                             message='仅使用字母数字和下划线')])
    # 密钥
    secret_key = models.CharField(max_length=128,
                                  validators=[RegexValidator(regex=r'^[_0-9a-zA-Z]+$',
                                                             message='仅使用字母数字和下划线')])
    # 是否启用
    enable = models.BooleanField(default=True)
    # 去哪里验证登陆信息
    login_auth_url = models.URLField(max_length=512, default='', blank=True)
    # access_token 在多少秒后过期
    access_token_ex = models.IntegerField(default=DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS)
    # refresh_token 在多少秒后过期
    refresh_token_ex = models.IntegerField(default=DEFAULT_REFRESH_TOKEN_EXPIRE_SECONDS)
    # 备注
    memo = models.CharField(blank=True, max_length=512)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dashboard'
        ordering = ['name']

    def to_json_dict(self, skip_id=False):
        d = {
            'name': self.name,
            'access_key': self.access_key,
            'secret_key': self.secret_key,
            'login_auth_url': self.login_auth_url,
            'access_token_ex': self.access_token_ex,
            'refresh_token_ex': self.refresh_token_ex,
            'enable': self.enable,
            'memo': self.memo
        }

        # 是否要过滤id
        if not skip_id:
            d['id'] = self.id

        if hasattr(self, 'endpoints'):
            d['endpoints'] = [t.to_json_dict(skip_id)
                              if isinstance(t, Endpoint) else t
                              for t in self.endpoints]

        return d

    def __unicode__(self):
        return self.name

    @classmethod
    def get_all_in_json(cls):
        data = Client.objects.all()
        return [t.to_json_dict() for t in data]

    @classmethod
    def get_client(cls, client_id):
        try:
            return Client.objects.get(id=client_id)
        except Exception as e:
            logger.debug(e)
            return None


class Endpoint(models.Model):
    """
    后端 API 的配置信息
    """
    # endpoint 的唯一名称, 可以使用中文, 由于可能存在多个相同的 name, 但是 url 或 uri 不一样
    # 因此需要有一个唯一的名称来区分
    unique_name = models.CharField(unique=True, max_length=128)
    # endpoint 名称, 需要使用在 url 上
    name = models.CharField(
        max_length=128,
        validators=[RegexValidator(
            regex=r'^[\-_0-9a-zA-Z]+$',
            message='仅使用字母数字和下划线')])

    version = models.CharField(
        max_length=128,
        validators=[RegexValidator(
            regex=r'^[\-_0-9a-zA-Z]+$',
            message='仅使用字母数字和下划线')])

    # 完整的URL，如 http://192.168.10.2:9090
    url = models.URLField(max_length=512, default='', blank=True)
    # 是否为内置的 endpoint, 如果是就可以不用输入 url
    is_builtin = models.BooleanField(default=False)
    # 是否启用访问控制列表
    enable_acl = models.BooleanField(default=False)
    # 是否启用 hmac 签名
    enable_hmac = models.BooleanField(default=True)
    # 配置超时时间，默认情况下 Tornado 是 20.0，避免有的网站很慢，需要很久才响应
    # Timeout for initial connection in seconds
    async_http_connect_timeout = models.IntegerField(
        default=DEFAULT_ASYNC_HTTP_CONNECT_TIMEOUT)
    # Timeout for entire request in seconds
    async_http_request_timeout = models.IntegerField(
        default=DEFAULT_ASYNC_HTTP_REQUEST_TIMEOUT)
    # 是否需要验证登陆
    require_login = models.BooleanField(default=False)

    # 备注
    memo = models.CharField(blank=True, max_length=512)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dashboard'
        ordering = ['name', 'version']
        db_table = 'dashboard_endpoint'

    def to_json_dict(self, skip_id=False):
        if self.url is not None:
            try:
                url_parsed = urlparse(self.url)
                netloc = url_parsed.netloc
            except Exception as e:
                logger.error(e)
                netloc = None
        else:
            netloc = None

        d = {
            'unique_name': self.unique_name,
            'name': self.name,
            'url': self.url,
            'is_builtin': self.is_builtin,
            'netloc': netloc,
            'version': self.version,
            'enable_acl': self.enable_acl,
            'enable_hmac': self.enable_hmac,
            'require_login': self.require_login,
            'async_http_connect_timeout': self.async_http_connect_timeout,
            'async_http_request_timeout': self.async_http_request_timeout,
            'memo': self.memo,
        }

        if hasattr(self, 'enable'):
            d['enable'] = self.enable

        # 是否要过滤id
        if not skip_id:
            d['id'] = self.id

        if hasattr(self, 'acl_rules'):
            d['acl_rules'] = [t.to_json_dict(skip_id) for t in self.acl_rules]

        return d

    def __unicode__(self):
        return self.name

    @classmethod
    def get_all_in_json(cls):
        data = Endpoint.objects.filter()
        for t in data:
            t.acl_rules = ACLRule.get_rules(t.id)

        return [t.to_json_dict() for t in data]


class ACLRule(models.Model):
    """
    访问控制列表，从上到下，依次匹配，如果未找到匹配项就允许访问
    """
    endpoint = models.ForeignKey(Endpoint)
    # . 表示匹配除换行符以外的任意字符
    re_uri = models.CharField(max_length=512)  # 正则表达式，需要匹配的URI
    is_permit = models.BooleanField(default=False)  # 是否允许访问
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dashboard'
        # 因为 ACLRule 表名会变成 dashboard_aclrule
        db_table = 'dashboard_acl_rule'

    def to_json_dict(self, skip_id=False):
        d = {
            're_uri': self.re_uri,
            'is_permit': self.is_permit
        }

        # 是否要过滤id
        if not skip_id:
            d['id'] = self.id
            d['endpoint_id'] = self.endpoint_id

        return d

    def __unicode__(self):
        return self.re_uri

    @classmethod
    def get_rules(cls, endpoint_id):
        return ACLRule.objects.filter(endpoint_id=endpoint_id)


class ClientEndpoint(models.Model):
    """
    client 可以访问的 endpoint
    """
    client = models.ForeignKey(Client)
    endpoint = models.ForeignKey(Endpoint)
    # 是否启用
    enable = models.BooleanField(default=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dashboard'
        db_table = 'dashboard_client_endpoint'

    def to_json_dict(self, skip_id=False):
        d = {
            'endpoint': self.endpoint.to_json_dict(),
            'enable': self.enable
        }

        # 是否要过滤id
        if not skip_id:
            d['id'] = self.id

        return d

    @classmethod
    def get_all_in_json(cls, client_id):
        data = ClientEndpoint.objects.select_related().filter(client_id=client_id)
        return [t.to_json_dict() for t in data]


class FileHandlerMixin(object):
    _headers_collection_name = None
    _body_collection_name = None

    @classmethod
    def delete_expired_headers_files(cls, expired_date):
        cls._delete_expired_gridfs_files(
            expired_date, cls._headers_collection_name)

    @classmethod
    def delete_expired_body_files(cls, expired_date):
        cls._delete_expired_gridfs_files(
            expired_date, cls._body_collection_name)

    @classmethod
    def _delete_expired_gridfs_files(cls, expired_date, collection_name):
        database = get_db()
        collection = database[collection_name]
        files = collection.files
        # chunks = collection.chunks
        # 只要删除files就可以，chunks会自动处理
        files.delete_many({"uploadDate": {'$lt': expired_date}})
        # chunks.delete_many({"uploadDate": {'$lt': expired_date}})

    @classmethod
    def delete_headers_files(cls, file_id_list):
        cls._delete_gridfs_files(file_id_list,
                                 cls._headers_collection_name)

    @classmethod
    def delete_body_files(cls, file_id_list):
        cls._delete_gridfs_files(file_id_list,
                                 cls._body_collection_name)

    @classmethod
    def _delete_gridfs_files(cls, file_id_list, collection_name):
        database = get_db()
        collection = database[collection_name]
        files = collection.files
        chunks = collection.chunks
        files.delete_many({"_id": {'$in': file_id_list}})
        chunks.delete_many({"files_id": {'$in': file_id_list}})

    def write_file(self, collection_name, data, content_type='', hash_id=False):
        if data is None or len(data) <= 0:
            return None

        db = get_db()
        fs = gridfs.GridFS(db, collection_name)
        # redis 中的数据是先编码成 base64, 这里要重新转换回来
        data = b64decode(data)
        content = BytesIO(utf8(data))
        if not hash_id:
            _id = fs.put(content, content_type=content_type)
            logger.debug(_id)
        else:
            md5 = hashlib.md5(content.getvalue()).hexdigest()
            # TODO 并发情况下, 这里会出问题, 导致可能有相同md5的数据
            # -1表示降序，找出时间最近的
            grid_out_cursor = fs.find({'md5': md5}).sort("uploadDate", -1).limit(1)
            # grid_out = fs.find_one({'md5': md5})
            for grid_out in grid_out_cursor:
                _id = grid_out._id
                # 更新一下上传日期，使用的是utc时间
                # 只要更新files就可以，chunks会自动处理
                db[collection_name].files.update_one(
                    {"_id": _id}, {"$set": {'uploadDate': datetime.utcnow()}}
                )
                # db[collection_name].chunks.update_one(
                #     {"files_id": _id}, {"$set": {'uploadDate': datetime.utcnow()}}
                # )

                # logger.debug(_id)
                # 直接让引用计数的 _id 等于 file 的 _id
                # 不再使用引用计数，因为引用计数可能出现不一致的问题
                # 也就是引用计数不为0，但是实际上已经没有access_log引用该文件
                # logger.debug(collection_name)
                # db['ref_%s' % collection_name].update({'_id': _id}, {'$inc': {'count': 1}}, upsert=True)
                break
            else:
                _id = fs.put(content, content_type=content_type)

        return _id

    def save_files(self, headers_content, body_content):
        self.headers.grid_id = self.write_file(
            self._headers_collection_name, headers_content, 'text/plain', True)
        logger.info(self.headers.grid_id)

        self.body.grid_id = self.write_file(
            self._body_collection_name, body_content, self.content_type, True)

        logger.info(self.body.grid_id)


class AccessLogRequest(EmbeddedDocument, FileHandlerMixin):
    _headers_collection_name = 'request_headers'
    _body_collection_name = 'request_body'

    method = StringField()
    content_type = StringField()
    headers = FileField(collection_name=_headers_collection_name)
    body = FileField(collection_name=_body_collection_name)
    uri = StringField()

    def to_json_dict(self):
        j = {
            'uri': self.uri,
            'method': self.method,
            'content_type': self.content_type,
            'headers_id': text_type(self.headers.grid_id),
            'body_id': text_type(self.body.grid_id)
        }
        if check_text_content_type(self.content_type):
            j['text_type'] = True
        else:
            j['text_type'] = False

        return j


class AccessLogResponse(EmbeddedDocument, FileHandlerMixin):
    _headers_collection_name = 'response_headers'
    _body_collection_name = 'response_body'

    status = IntField()
    content_type = StringField()
    headers = FileField(collection_name=_headers_collection_name)
    body = FileField(collection_name=_body_collection_name)

    def to_json_dict(self):
        j = {
            'status': self.status,
            'content_type': self.content_type,
            'headers_id': text_type(self.headers.grid_id),
            'body_id': text_type(self.body.grid_id)
        }
        if check_text_content_type(self.content_type):
            j['text_type'] = True
        else:
            j['text_type'] = False

        return j


class AccessLogClient(EmbeddedDocument):
    id = IntField()
    name = StringField()

    def to_json_dict(self):
        j = {
            'id': self.id,
            'name': self.name,
        }
        return j


class AccessLogEndpoint(EmbeddedDocument):
    id = IntField()
    name = StringField()
    is_builtin = BooleanField(default=False)
    version = StringField()

    def to_json_dict(self):
        j = {
            'id': self.id,
            'name': self.name,
            'is_builtin': self.is_builtin,
            'version': self.version
        }
        return j


class AccessLog(DynamicDocument):
    # 转发到哪个 URL
    forward_url = StringField(default='')

    # 请求的数据
    request = EmbeddedDocumentField(AccessLogRequest)
    # 响应的数据
    response = EmbeddedDocumentField(AccessLogResponse)

    client = EmbeddedDocumentField(AccessLogClient)
    endpoint = EmbeddedDocumentField(AccessLogEndpoint)
    ip = StringField()
    # 请求的时间
    accessed_at = DateTimeField()
    elapsed = IntField()
    # 返回结果的编码
    result_code = IntField()
    result_msg = StringField()
    # 是否被数据统计任务处理过
    flag = BooleanField(default=False)

    meta = {
        'collection': 'access_log',
        'indexes': [
            '-id',
            ('-accessed_at', '-id'),
            ('-accessed_at', '-id', 'result_code'),
            ('-accessed_at', '-id', 'client.id'),
            ('-accessed_at', '-id', 'client.id', 'endpoint.id')
        ]
    }

    def to_json_dict(self):
        j = {
            'id': text_type(self.id),
            'forward_url': self.forward_url,
            'timestamp': datetime_to_timestamp(self.accessed_at),
            'accessed_at': datetime_to_str(self.accessed_at, '%Y-%m-%d %H:%M:%S'),
            'elapsed': self.elapsed,
            'result_code': self.result_code,
            'result_msg': self.result_msg,
            'ip': self.ip,
            'request': self.request.to_json_dict(),
            'response': self.response.to_json_dict(),
            'client': self.client.to_json_dict(),
            'endpoint': self.endpoint.to_json_dict()
        }

        return j

    @classmethod
    def query(cls, **kwargs):
        filter_dict = {}
        map_dict = {
            'begin_time': 'accessed_at__gte',
            'end_time': 'accessed_at__lte',
            'ip_list': 'ip__in',
            'status_list': 'status__in',
            'ip': 'ip__icontains',
            'uri': 'request__uri__icontains',
            'status': 'response__status',
            'elapsed_min': 'elapsed__gte',
            'elapsed_max': 'elapsed__lte',
            'selected_clients': 'client__id__in',
            'selected_endpoints': 'endpoint__id__in',
            'selected_results': 'result_code__in',
        }
        for k, v in map_dict.items():
            field = kwargs.get(k)
            if isinstance(field, list) and len(field) == 0:
                continue

            if field is not None and field != '':
                filter_dict[v] = kwargs.get(k)

        last_item = kwargs.get('last_item')
        if last_item is not None:
            # accessed_at = datetime.fromtimestamp(last_item['timestamp'] / 1000.0)
            # filter_dict['accessed_at__lte'] = accessed_at
            filter_dict['id__lt'] = last_item['id']

        # 因为是按照 id 排序的, 不能保证返回的数据是按创建的时间排序
        # 因为 id 只能保证在秒的级别是由先后顺序的
        order_by = ['-id']
        limit = kwargs.get('limit', DEFAULT_ACCESS_LOG_PAGE_SIZE)
        logger.debug(limit)
        skip = kwargs.get('skip', 0)
        logger.debug(skip)
        logs = AccessLog.objects(**filter_dict).no_dereference().order_by(
            *order_by)[skip:skip + limit]
        logs = [t.to_json_dict() for t in logs]

        if kwargs.get('require_total_num'):
            if 'id__lt' in filter_dict:
                del filter_dict['id__lt']
            total_num = AccessLog.objects(**filter_dict).count()
        else:
            total_num = None

        return logs, total_num

    @classmethod
    def get_detail(cls, **kwargs):
        data_type = kwargs['data_type']
        if data_type == 'request':
            model_cls = AccessLogRequest
        else:
            model_cls = AccessLogResponse

        entry = model_cls()
        body_id = kwargs.get('body_id')
        if body_id and body_id != 'None':
            entry.body.grid_id = ObjectId(body_id)
            body = entry.body.read()
            return body

        headers_id = kwargs.get('headers_id')
        if headers_id and headers_id != 'None':
            entry.headers.grid_id = ObjectId(headers_id)
            headers = entry.headers.read()
            return headers

        return ''


class AccessTotalDayCounter(DynamicDocument):
    """
    所有访问量, 按天的计数
    """
    count = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_total_day',
        'indexes': [
            ('-date', '-id'),
        ]
    }


class AccessTotalHourCounter(DynamicDocument):
    """
    所有访问量, 按小时的计数
    """
    count = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_total_hour',
        'indexes': [
            ('-date', '-id'),
        ]
    }


class AccessDayCounter(DynamicDocument):
    """
    访问应用和端点, 按天的访问计数
    """
    count = IntField()
    endpoint_id = IntField()
    client_id = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_access_day',
        'indexes': [
            ('-date', '-id'),
            ('-date', 'client.id', 'endpoint.id'),
            ('-date', 'endpoint.id')
        ]
    }


class AccessHourCounter(DynamicDocument):
    """
    访问应用和端点, 按小时的访问计数
    """
    count = IntField()
    endpoint_id = IntField()
    client_id = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_access_hour',
        'indexes': [
            ('-date', '-id'),
            ('-date', 'client.id', 'endpoint.id'),
            ('-date', 'endpoint.id')
        ]
    }


class AccessResultDayCounter(DynamicDocument):
    """
    访问结果, 按天的访问计数
    """
    count = IntField()
    code = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_result_day',
        'indexes': [
            ('-date', 'code'),
        ]
    }


class AccessResultHourCounter(DynamicDocument):
    """
    访问结果, 按小时的访问计数
    """
    count = IntField()
    code = IntField()
    date = DateTimeField()

    meta = {
        'collection': 'counter_result_hour',
        'indexes': [
            ('-date', 'code'),
        ]
    }


def _render_time_frame_data(unit, time_frame, name_map, data, data_type, count_list_dict):
    count_data = []
    if unit == 'hour':
        dk_format = '%Y-%m-%d %H'
    else:
        dk_format = '%Y-%m-%d'

    if data_type == 'total':
        count_dict = {}
        for t in data:
            k = t.date.strftime(dk_format)
            count_dict[k] = t.count

        temp_data = []
        for t in time_frame:
            temp_data.append(count_dict.get(t, 0))

        name = name_map.get('total', '全部应用')
        count_data.append([name, temp_data])
    elif data_type in ['client', 'endpoint']:
        # count_list_dict = {}
        k_field = data_type + '_id'
        for t in data:
            k = t['_id'][k_field]
            dk = t['_id']['date'].strftime(dk_format)
            if k in count_list_dict:
                count_list_dict[k][dk] = t['count']
            else:
                count_list_dict[k] = {dk: t['count']}

        for k, v in count_list_dict.items():
            temp_data = []
            for t in time_frame:
                temp_data.append(v.get(t, 0))

            name = name_map[data_type].get(text_type(k), text_type(k))
            count_data.append([name, temp_data])
    elif data_type == 'client_endpoint':
        # count_list_dict = {}
        for t in data:
            k = '%s/%s' % (t['_id']['client_id'], t['_id']['endpoint_id'])
            dk = t['_id']['date'].strftime(dk_format)
            if k in count_list_dict:
                count_list_dict[k][dk] = t['count']
            else:
                count_list_dict[k] = {dk: t['count']}

        for k, v in count_list_dict.items():
            temp_data = []
            for t in time_frame:
                temp_data.append(v.get(t, 0))

            name = name_map[data_type].get(text_type(k), text_type(k))
            count_data.append([name, temp_data])
    elif data_type == 'result_code':
        # count_list_dict = {}
        for t in data:
            k = t['_id']['code']
            dk = t['_id']['date'].strftime(dk_format)
            if k in count_list_dict:
                count_list_dict[k][dk] = t['count']
            else:
                count_list_dict[k] = {dk: t['count']}

        for k, v in count_list_dict.items():
            temp_data = []
            for t in time_frame:
                temp_data.append(v.get(t, 0))

            name = name_map[data_type].get(text_type(k), text_type(k))
            count_data.append([name, temp_data])
    return count_data


def _get_model_cls_by_unit(time_unit, data_type):
    if time_unit == 'hour':
        if data_type == 'total':
            return AccessTotalHourCounter
        elif data_type == 'result_code':
            return AccessResultHourCounter
        else:
            return AccessHourCounter
    else:
        if data_type == 'total':
            return AccessTotalDayCounter
        elif data_type == 'result_code':
            return AccessResultDayCounter
        else:
            return AccessDayCounter


def query_access_count(**kwargs):
    count_data = []
    client_list = kwargs.get('client_list', [])
    endpoint_list = kwargs.get('endpoint_list', [])
    client_endpoint_list = kwargs.get('client_endpoint_list', [])
    result_code_list = kwargs.get('result_code_list', [])
    name_map = kwargs.get('name_map', {})
    # 时间单位, 时或者天
    time_unit = kwargs.get('time_unit')
    require_total = kwargs.get('require_total', False)
    begin_time = kwargs.get('begin_time', None)
    end_time = kwargs.get('end_time', None)
    filter_dict = {}
    time_frame = []
    for i, t in enumerate(client_list):
        if t == '-1':
            require_total = True
            client_list.pop(i)

    if begin_time is not None:
        filter_dict['date__gte'] = begin_time
    if end_time is not None:
        filter_dict['date__lte'] = end_time

    now = datetime.now()
    x_data = []
    if time_unit == 'hour':
        if end_time is None:
            end_time = datetime(now.year, now.month, now.day, now.hour)

        dt = datetime(begin_time.year, begin_time.month, begin_time.day, begin_time.hour)
        x_data_use_hour = kwargs.get('x_data_use_hour', False)
        while dt <= end_time:
            time_frame.append(dt.strftime('%Y-%m-%d %H'))
            if x_data_use_hour:
                x_data.append(dt.hour)
            else:
                x_data.append(dt.strftime('%m-%d %H'))
            dt += timedelta(hours=1)
    else:
        if end_time is None:
            end_time = datetime(now.year, now.month, now.day)

        dt = datetime(begin_time.year, begin_time.month, begin_time.day)
        while dt <= end_time:
            time_frame.append(dt.strftime('%Y-%m-%d'))
            x_data.append(dt.strftime('%m-%d'))
            dt += timedelta(days=1)

    if require_total:
        model_cls = _get_model_cls_by_unit(time_unit, 'total')
        count_total_list = model_cls.objects(**filter_dict)
        ret_data = _render_time_frame_data(time_unit, time_frame, name_map,
                                           count_total_list, 'total', None)
        count_data.extend(ret_data)

    if len(client_list) > 0:
        pipeline = [
            {
                "$group": {
                    "_id": {"date": "$date", "client_id": "$client_id"},
                    "count": {"$sum": "$count"}
                }
            }
        ]
        model_cls = _get_model_cls_by_unit(time_unit, 'client')
        count_client_list = model_cls.objects(
            client_id__in=client_list, **filter_dict).aggregate(*pipeline)
        count_list_dict = {}
        for t in client_list:
            count_list_dict[t] = {}

        ret_data = _render_time_frame_data(time_unit, time_frame, name_map,
                                           count_client_list, 'client', count_list_dict)
        count_data.extend(ret_data)

    if len(endpoint_list) > 0:
        pipeline = [
            {
                "$group": {
                    "_id": {"date": "$date", "endpoint_id": "$endpoint_id"},
                    "count": {"$sum": "$count"}
                }
            }
        ]
        model_cls = _get_model_cls_by_unit(time_unit, 'endpoint')
        count_endpoint_list = model_cls.objects(
            endpoint_id__in=endpoint_list, **filter_dict).aggregate(*pipeline)
        count_list_dict = {}
        for t in endpoint_list:
            count_list_dict[t] = {}
        ret_data = _render_time_frame_data(time_unit, time_frame, name_map,
                                           count_endpoint_list, 'endpoint', count_list_dict)
        count_data.extend(ret_data)

    if len(client_endpoint_list) > 0:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "date": "$date",
                        "client_id": "$client_id",
                        "endpoint_id": "$endpoint_id"
                    },
                    "count": {"$sum": "$count"}
                }
            }
        ]

        t_client_list = set([t[0] for t in client_endpoint_list])
        t_endpoint_list = set([t[1] for t in client_endpoint_list])
        model_cls = _get_model_cls_by_unit(time_unit, 'client_endpoint')
        count_client_endpoint_list = model_cls.objects(
            client_id__in=t_client_list, endpoint_id__in=t_endpoint_list,
            **filter_dict).aggregate(*pipeline)
        count_list_dict = {}
        for t in client_endpoint_list:
            k = '%s/%s' % (t[0], t[1])
            count_list_dict[k] = {}
        ret_data = _render_time_frame_data(time_unit, time_frame, name_map,
                                           count_client_endpoint_list,
                                           'client_endpoint', count_list_dict)
        count_data.extend(ret_data)
    if len(result_code_list) > 0:
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "date": "$date",
                        "code": "$code"
                    },
                    "count": {"$sum": "$count"}
                }
            }
        ]
        model_cls = _get_model_cls_by_unit(time_unit, 'result_code')
        count_result_code_list = model_cls.objects(
            code__in=result_code_list, **filter_dict).aggregate(*pipeline)
        count_list_dict = {}
        for t in result_code_list:
            count_list_dict[t] = {}
        ret_data = _render_time_frame_data(time_unit, time_frame, name_map,
                                           count_result_code_list,
                                           'result_code', count_list_dict)
        count_data.extend(ret_data)

    return x_data, count_data


def get_export_config_json(skip_id=False):
    """
    获取导出配置的json数据
    :return:
    """
    clients = Client.objects.all()
    endpoints = Endpoint.objects.all()
    acl_rules = ACLRule.objects.all()
    client_endpoints = ClientEndpoint.objects.all()

    acl_rules_dict = {}
    for t in acl_rules:
        if t.endpoint_id in acl_rules_dict:
            acl_rules_dict[t.endpoint_id].append(t)
        else:
            acl_rules_dict[t.endpoint_id] = [t]

    for t in endpoints:
        t.acl_rules = acl_rules_dict.get(t.id, [])

    client_endpoint_list = []
    for t in client_endpoints:
        d = {
            'client_id': t.client_id,
            'endpoint_id': t.endpoint_id,
            'enable': t.enable
        }

        if not skip_id:
            d['id'] = t.id

        client_endpoint_list.append(d)

    json_data = {
        'clients': [t.to_json_dict(skip_id) for t in clients],
        'endpoints': [t.to_json_dict(skip_id) for t in endpoints],
        'client_endpoints': client_endpoint_list
    }

    return json_data


def get_config_redis_json():
    """
    获取将要存储在redis中的配置json数据
    :return:
    """
    clients = Client.objects.filter(enable=True)
    endpoints = Endpoint.objects.all()
    acl_rules = ACLRule.objects.all()
    client_endpoints = ClientEndpoint.objects.filter(enable=True)

    acl_rules_dict = {}
    for t in acl_rules:
        if t.endpoint_id in acl_rules_dict:
            acl_rules_dict[t.endpoint_id].append(t)
        else:
            acl_rules_dict[t.endpoint_id] = [t]

    endpoint_dict = {}
    for t in endpoints:
        t.acl_rules = acl_rules_dict.get(t.id, [])
        endpoint_dict[t.id] = t

    client_endpoint_dict = {}
    for t in client_endpoints:
        endpoint = endpoint_dict[t.endpoint_id]
        endpoint.enable = t.enable
        if t.client_id in client_endpoint_dict:
            client_endpoint_dict[t.client_id].append(endpoint)
        else:
            client_endpoint_dict[t.client_id] = [endpoint]

    json_data = [t.to_json_dict() for t in clients]
    for t in json_data:
        e_dict = {}
        endpoints = client_endpoint_dict.get(t['id'], [])
        endpoints = [x.to_json_dict() for x in endpoints]
        for x in endpoints:
            k = '%s:%s' % (x['name'], x['version'])
            e_dict[k] = x
        t['endpoints'] = e_dict

    return json_data
