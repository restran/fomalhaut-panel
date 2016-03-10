# -*- coding: utf-8 -*-
# created by restran on 2016/03/06
from __future__ import unicode_literals

import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
import logging
from common.utils import http_response_json
from accounts.decorators import login_required

from . import access_log
from . import config
from . import dashboard
from ..models import *

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
@require_http_methods(["GET"])
def get_options(request):
    """
    获取 client, endpoint, client_endpoint select 选项
    """
    success, msg, data = False, '', []
    clients = Client.objects.all().values('id', 'name')
    clients = [t for t in clients]
    endpoints = Endpoint.objects.all().values('id', 'unique_name')
    endpoints = [
        {
            'id': t['id'],
            'unique_name': t['unique_name'],
        } for t in endpoints
        ]
    client_endpoints = ClientEndpoint.objects.all().values(
        'id', 'client_id', 'endpoint_id')
    client_dict = {}
    for t in clients:
        client_dict[t['id']] = t['name']

    endpoint_dict = {}
    for t in endpoints:
        endpoint_dict[t['id']] = t['unique_name']

    new_client_endpoints = []
    for t in client_endpoints:
        new_client_endpoints.append({
            'id': t['id'],
            'name': '%s / %s' % (
                client_dict.get(t['client_id'], ''),
                endpoint_dict.get(t['endpoint_id'], '')
            ),
            'client_id': t['client_id'],
            'endpoint_id': t['endpoint_id']
        })

    data = {
        'clients': clients,
        'endpoints': endpoints,
        'client_endpoints': new_client_endpoints
    }
    success = True
    logger.debug(data)
    return http_response_json({'success': success, 'msg': msg, 'data': data})


@login_required
@csrf_protect
@require_http_methods(["GET"])
def get_client_options(request):
    """
    获取 Client select 选项
    """
    success, msg, data = False, '', []
    data = Client.objects.all().values('id', 'name')
    data = [t for t in data]
    success = True
    logger.debug(data)
    return http_response_json({'success': success, 'msg': msg, 'data': data})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def get_endpoint_options(request):
    """
    获取 Endpoint select 选项
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    clients = post_data.get('clients', [])

    if len(clients) == 0:
        data = Endpoint.objects.all().values('id', 'unique_name', 'name', 'version')
        data = [
            {
                'id': t['id'],
                'unique_name': t['unique_name'],
                'name': t['name'],
                'version': t['version']
            } for t in data
            ]
    else:
        data = ClientEndpoint.objects.filter(
            client_id__in=clients).select_related('endpoint')
        data = [
            {
                'id': t.endpoint.id,
                'unique_name': t.endpoint.unique_name,
                'name': t.endpoint.name,
                'version': t.endpoint.version
            }
            for t in data
            ]

    success = True
    logger.debug(data)
    return http_response_json({'success': success, 'msg': msg, 'data': data})
