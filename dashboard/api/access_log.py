# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

import json

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.http import HttpResponse
from common.utils import http_response_json, utf8, json_loads
from accounts.decorators import login_required
import logging
from ..models import AccessLog
from ..tasks import transfer_access_logs, parse_access_logs
from datetime import datetime
from base64 import b64encode
from fomalhaut.settings import ACCESS_LOG_DETAIL_MAX_BODY_LENGTH

logger = logging.getLogger(__name__)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def get_access_log(request):
    """
    获取访问日志
    :param request:
    :return:
    """
    success, msg, data = False, '', []
    post_data = json_loads(request.body)
    if post_data['begin_time'] != '' and post_data['begin_time'] is not None:
        post_data['begin_time'] = datetime.strptime(post_data['begin_time'], '%Y-%m-%d %H:%M')

    if post_data['end_time'] != '' and post_data['end_time'] is not None:
        post_data['end_time'] = datetime.strptime(post_data['end_time'], '%Y-%m-%d %H:%M')

    entries, total_num = AccessLog.query(**post_data)
    data = {
        'entries': entries,
        'total_num': total_num
    }
    # logger.debug(data)
    return http_response_json({'success': True, 'msg': msg, 'data': data})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def get_access_detail(request):
    """
    获取访问日志的详情
    :param request:
    :return:
    """
    success, msg, data = False, '', []
    post_data = json_loads(request.body)
    data = AccessLog.get_detail(**post_data)
    if post_data.get('headers_id') is not None:
        return http_response_json({'success': True, 'msg': msg, 'data': data})
    else:
        if data and len(data) > ACCESS_LOG_DETAIL_MAX_BODY_LENGTH:
            data = data[:ACCESS_LOG_DETAIL_MAX_BODY_LENGTH]
        return HttpResponse(data)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_refresh_access_log(request):
    """
    立即从redis中更新访问日志
    :param request:
    :return:
    """
    success, msg, data = False, '', []
    transfer_access_logs.delay()
    parse_access_logs.delay()
    return http_response_json({'success': True, 'msg': msg})
