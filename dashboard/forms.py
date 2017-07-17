# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import *
from common.forms import BaseModelForm

logger = logging.getLogger(__name__)


class ClientForm(BaseModelForm):
    class Meta:
        model = Client
        fields = ('name', 'memo', 'enable', "app_id", 'secret_key',
                  'login_auth_url', 'access_token_ex', 'refresh_token_ex',
                  'sms_login_auth_url', 'change_password_url', 'sms_change_password_url')

    def clean_refresh_token_ex(self):
        access_token_ex = self.cleaned_data['access_token_ex']
        refresh_token_ex = self.cleaned_data['refresh_token_ex']
        if access_token_ex >= refresh_token_ex:
            raise forms.ValidationError(_('refresh_token 的过期时间不能小于 access_token'))

        return refresh_token_ex


ClientForm.base_fields.keyOrder = [
    'name', 'memo', 'url', 'enable', 'app_id',
    'secret_key', 'login_auth_url', 'access_token_ex',
    'refresh_token_ex', 'sms_login_auth_url', 'sms_change_password_url',
    'change_password_url'
]


#
# class ClientEndpointForm(BaseModelForm):
#     class Meta:
#         model = Client
#         fields = ('name', 'memo', 'enable', 'access_key', 'secret_key')


class EndpointForm(BaseModelForm):
    def __init__(self, *args, **kwargs):
        super(EndpointForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Endpoint
        fields = ('name', 'is_builtin', 'url', 'unique_name', 'enable_acl', 'version',
                  'async_http_connect_timeout', 'async_http_request_timeout', 'enable_hmac',
                  'memo', 'require_login')

    def clean_url(self):
        is_builtin = self.cleaned_data['is_builtin']
        url = self.cleaned_data['url']
        if not is_builtin and (url is None or url == ''):
            raise forms.ValidationError(_('Endpoint URL 不能为空'))
        else:
            return url

    def clean_unique_name(self):
        unique_name = self.cleaned_data['unique_name']
        if self.instance is not None:
            sites = Endpoint.objects.filter(unique_name=unique_name).values('id')
            for t in sites:
                if t['id'] != self.instance.id:
                    raise forms.ValidationError(_('已存在相同名称的 Endpoint'))
        else:
            sites = Endpoint.objects.filter(unique_name=unique_name).values('id')
            if len(sites) > 0:
                raise forms.ValidationError(_('已存在相同名称的 Endpoint'))
        return unique_name


EndpointForm.base_fields.keyOrder = [
    'name', 'unique_name', 'is_builtin', 'url', 'prefix_uri', 'enable_acl',
    'async_http_connect_timeout', 'async_http_request_timeout', 'enable_hmac',
    'memo', 'require_login']


class ACLRuleForm(BaseModelForm):
    class Meta:
        model = ACLRule
        fields = ('re_uri', 'is_permit')
