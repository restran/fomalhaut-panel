# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
import logging
from urlparse import urlparse

from django.db import models

from django.core.validators import RegexValidator

from api_dashboard.settings import DEFAULT_ASYNC_HTTP_CONNECT_TIMEOUT, DEFAULT_ASYNC_HTTP_REQUEST_TIMEOUT
from common.utils import datetime_to_str
from api_dashboard.settings import DEFAULT_ACCESS_LOG_PAGE_SIZE

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
        default='',
        blank=True,
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
    require_app_login = models.BooleanField(default=True)
    login_verify_url = models.URLField(max_length=512)
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


class AccessLog(models.Model):
    """
    访问日志
    """
    url = models.CharField(max_length=1024)
    # 访问结果编码
    result_code = models.CharField(max_length=2, choices=ACCESS_RESULT_TYPE,
                                   default=ACCESS_RESULT_UNKNOWN)
    agent_id = models.IntegerField(db_index=True, null=True)
    site_id = models.IntegerField(null=True)
    agent_name = models.CharField(max_length=512)
    site_name = models.CharField(max_length=512)
    time = models.DateTimeField()
    remote_ip = models.CharField(max_length=512)
    status_code = models.IntegerField(null=True)
    # 耗时
    elapsed = models.IntegerField(default=-1)
    # 访问方法， GET 或 POST
    method = models.CharField(max_length=40, default='GET')
    # 鉴权的令牌是否在 header 中，用来判断是否属于页面浏览
    header_token = models.BooleanField(default=False)
    date = models.DateField(db_index=True)
    hour = models.IntegerField()

    class Meta:
        app_label = 'dashboard'
        db_table = 'dashboard_access_log'
        index_together = [
            ['time', 'result_code'], ['time', 'agent_id'],
        ]

    def to_json_dict(self):
        d = {
            'id': self.id,
            'url': self.url,
            'result_code': self.result_code,
            'access_result': choice_id_to_name(ACCESS_RESULT_TYPE, self.result_code),
            'agent_id': self.agent_id,
            'site_id': self.site_id,
            'agent_name': self.agent_name,
            'site_name': self.site_name, 'remote_ip': self.remote_ip,
            'status_code': self.status_code,
            'method': self.method,
            'time': datetime_to_str(self.time),
            'header_token': self.header_token,
            'elapsed': self.elapsed
        }

        return d

    @classmethod
    def get_page_in_json(cls, date, agent_id_list, result_code_list, page_id=1):
        page_size = DEFAULT_ACCESS_LOG_PAGE_SIZE
        offset = page_size * (page_id - 1)
        logger.debug(page_id)
        logger.debug(page_size)

        if agent_id_list is None:
            if result_code_list is None:
                data = AccessLog.objects.filter(
                    date=date).order_by('-time')[offset:offset + page_size + 1]
            else:
                data = AccessLog.objects.filter(
                    date=date,
                    result_code__in=result_code_list).order_by('-time')[offset:offset + page_size + 1]
        else:
            if result_code_list is None:
                # 多取1个，是为了判断是否有 next
                data = AccessLog.objects.filter(
                    date=date,
                    agent_id__in=agent_id_list).order_by('-time')[offset:offset + page_size + 1]
            else:
                # 多取1个，是为了判断是否有 next
                data = AccessLog.objects.filter(
                    date=date,
                    agent_id__in=agent_id_list,
                    result_code__in=result_code_list).order_by('-time')[offset:offset + page_size + 1]

        json_list = []
        for t in data:
            json_list.append(t.to_json_dict())

        has_next_page = False
        length = len(data)
        if length > page_size:
            json_list = json_list[:-1]
            has_next_page = True
            if agent_id_list is None:
                if result_code_list is None:
                    total_num = AccessLog.objects.filter(
                        date=date).count()
                else:
                    total_num = AccessLog.objects.filter(
                        date=date,
                        result_code__in=result_code_list).count()
            else:
                if result_code_list is None:
                    total_num = AccessLog.objects.filter(
                        date=date,
                        agent_id__in=agent_id_list).count()
                else:
                    total_num = AccessLog.objects.filter(
                        date=date,
                        agent_id__in=agent_id_list,
                        result_code__in=result_code_list).count()

        elif length > 0:
            total_num = offset + length
        else:
            # length为0，表示这一页为空，或者不应该有这一页
            # 显示这一页为空
            total_num = offset  # total_num <= offset

        if offset > 0:
            has_previous_page = True
        else:
            has_previous_page = False

        return json_list, total_num, has_previous_page, has_next_page, offset


class AccessDayCounter(models.Model):
    """
    累计访问计数
    """
    count = models.IntegerField()
    # 是否是页面浏览，代理的请求中会有很多页面内的css和js文件的请求
    # 通过判断令牌信息是否位于 header 中来判断
    # 因为css和js文件的请求目前不能在 header 中放令牌信息，只能通过 cookie
    page_view = models.BooleanField(default=False)
    date = models.DateField()

    class Meta:
        app_label = 'dashboard'
        db_table = 'dashboard_access_day_counter'
        index_together = [
            ['date', 'page_view']
        ]


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
        'client': [t.to_json_dict(skip_id) for t in clients],
        'endpoints': [t.to_json_dict(skip_id) for t in endpoints],
        'client_endpoints': client_endpoint_list
    }

    return json_data
