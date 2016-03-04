# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
from django.conf.urls import url
from dashboard import views, api

model_name_regex = r'(?P<model_name>client|endpoint|client_endpoint)'

urlpatterns = [
    url(r'^$', views.dashboard),
    url(r'^dashboard/$', views.dashboard),
    url(r'^dashboard/access_log/$', views.access_log),
    url(r'^dashboard/config/$', views.config),
    url(r'^dashboard/config/action/export/$', views.export_config),
    url(r'^dashboard/config/(?P<data_type>[a-z0-9A-Z_-]+)/$', views.config),
    url(r'^dashboard/help/(?P<page_name>[a-z0-9A-Z_-]+)/$', views.help_page),
]

urlpatterns.extend([
    url(r'^api/dashboard/' + model_name_regex + '/$',
        api.api_get_model_data),
    url(r'^api/dashboard/' + model_name_regex + '/create/$',
        api.api_create_model_data),
    url(r'^api/dashboard/' + model_name_regex + '/(?P<entry_id>\d+)/update/$',
        api.api_update_model_data),
    url(r'^api/dashboard/' + model_name_regex + '/(?P<entry_id>\d+)/delete/$',
        api.api_delete_model_data),
    url(r'^api/dashboard/' + model_name_regex + '/(?P<entry_id>\d+)/update_enable_state/$',
        api.api_update_enable_state_model_data),
    url(r'^api/dashboard/upload/import/$',
        api.api_import_config),

    url(r'^api/dashboard/transfer-to-redis/$', api.api_transfer_to_redis),
    url(r'^api/dashboard/get_total_by_day_access/$', api.api_get_total_by_day_access),
    url(r'^api/dashboard/get_total_by_month_access/$', api.api_get_total_by_month_access),
    url(r'^api/dashboard/get_total_count/$', api.api_get_total_count),
    url(r'^api/dashboard/get_options/$', api.api_get_options),
    url(r'^api/dashboard/get_client_options/$', api.api_get_client_options),
    url(r'^api/dashboard/get_endpoint_options/$', api.api_get_endpoint_options),
    url(r'^api/dashboard/get_ip_count/$', api.api_get_ip_count),
    url(r'^api/dashboard/get_abnormal_ip_count/$', api.api_get_abnormal_ip_count),
    url(r'^api/dashboard/access_log/query/$', api.api_get_access_log),
    url(r'^api/dashboard/access_log/refresh/$', api.api_refresh_access_log),
])
