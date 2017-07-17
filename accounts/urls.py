# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from . import views, api

# 元组是可累加的，但累加后是生成新的元组，而非在原来的基础上修改
urlpatterns = [
    url(r'^accounts/login/$', views.user_login),
    url(r'^accounts/logout/$', views.user_logout),
    url(r'^accounts/create_admin/$', views.create_admin),
    url(r'^accounts/manage/$', views.manage_accounts),
    url(r'^accounts/password/reset_confirm/(?P<user_id>\d+)/(?P<token>[^/]+)/$', views.password_reset_confirm),
    url(r'^accounts/password/reset_request/$', views.password_reset_request),
    url(r'^accounts/profile/$', views.account_profile),
]

urlpatterns.extend([
    url(r'^api/accounts/create_admin/$', api.api_create_admin),
    url(r'^api/accounts/$', api.api_get_accounts),
    url(r'^api/accounts/user_login/$', api.api_user_login),
    url(r'^api/accounts/delete/$', api.api_delete_account),
    url(r'^api/accounts/update/(?P<user_id>\d*)/$', api.api_update_account),
    url(r'^api/accounts/create/$', api.api_create_account),
    url(r'^api/accounts/password/update/$', api.api_update_password),
    url(r'^api/accounts/password/reset/$', api.api_reset_password),
    url(r'^api/accounts/password/reset_request/$', api.reset_password_request),
])
