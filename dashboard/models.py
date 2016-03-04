# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
from datetime import datetime
import logging
from urlparse import urlparse

from django.db import models

from django.core.validators import RegexValidator

from api_dashboard.settings import DEFAULT_ASYNC_HTTP_CONNECT_TIMEOUT, \
    DEFAULT_ASYNC_HTTP_REQUEST_TIMEOUT, DEFAULT_ACCESS_TOKEN_EXPIRE_SECONDS, \
    DEFAULT_REFRESH_TOKEN_EXPIRE_SECONDS
from common.utils import datetime_to_str, datetime_to_timestamp
from api_dashboard.settings import DEFAULT_ACCESS_LOG_PAGE_SIZE
from mongoengine import *
from six import text_type

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
            logger.debug(e.message)
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
    url = models.URLField(max_length=512)
    # 是否启用访问控制列表
    enable_acl = models.BooleanField(default=False)

    # 配置超时时间，默认情况下 Tornado 是 20.0，避免有的网站很慢，需要很久才响应
    # Timeout for initial connection in seconds
    async_http_connect_timeout = models.IntegerField(
        default=DEFAULT_ASYNC_HTTP_CONNECT_TIMEOUT)
    # Timeout for entire request in seconds
    async_http_request_timeout = models.IntegerField(
        default=DEFAULT_ASYNC_HTTP_REQUEST_TIMEOUT)
    # 是否需要验证登陆
    require_login = models.BooleanField(default=True)

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
            'netloc': netloc,
            'version': self.version,
            'enable_acl': self.enable_acl,
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
            'enable': self.enable,
        }

        # 是否要过滤id
        if not skip_id:
            d['id'] = self.id

        return d

    @classmethod
    def get_all_in_json(cls, client_id):
        data = ClientEndpoint.objects.select_related().filter(client_id=client_id)
        return [t.to_json_dict() for t in data]


# 访问结果类型
ACCESS_RESULT_SUCCESS = '0'  # 成功
ACCESS_RESULT_FORBIDDEN = '1'  # 禁止访问
ACCESS_RESULT_PROXY_FAILED = '2'  # 代理失败
ACCESS_RESULT_LOGIN_VALIDATED_FAILED = '3'  # 验证App登录失败
ACCESS_RESULT_UNKNOWN = '4'  # 未知
ACCESS_RESULT_EXPIRED_TOKEN = '5'  # 鉴权令牌过期

ACCESS_RESULT_TYPE = (
    (ACCESS_RESULT_SUCCESS, 'Success'),
    (ACCESS_RESULT_FORBIDDEN, 'Forbidden'),
    (ACCESS_RESULT_PROXY_FAILED, 'Proxy Failed'),
    (ACCESS_RESULT_LOGIN_VALIDATED_FAILED, 'Login Validated Failed'),
    (ACCESS_RESULT_UNKNOWN, 'Unknown'),
    (ACCESS_RESULT_EXPIRED_TOKEN, 'Expired Token')
)


def choice_id_to_name(choice, c_id):
    """
    models 中，对于choice，将其从id转换为名称
    """
    for c in choice:
        if c[0] == c_id:
            return c[1]

    return ''


class AccessLogRequest(EmbeddedDocument):
    method = StringField()
    content_type = StringField()
    headers = FileField(collection_name='response_headers')
    body = FileField(collection_name='response_body')
    uri = StringField()

    def to_json_dict(self):
        j = {
            'uri': self.uri,
            'method': self.method,
            'content_type': self.content_type,
            'headers_id': self.headers.grid_id,
            'body_id': self.body.grid_id
        }
        return j


class AccessLogResponse(EmbeddedDocument):
    status = IntField()
    content_type = StringField()
    headers = FileField(collection_name='response_headers')
    body = FileField(collection_name='response_body')

    def to_json_dict(self):
        j = {
            'status': self.status,
            'content_type': self.content_type,
            'headers_id': self.headers.grid_id,
            'body_id': self.body.grid_id
        }
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
        for k, v in map_dict.iteritems():
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
