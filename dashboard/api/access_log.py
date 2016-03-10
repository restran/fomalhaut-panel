# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

import json

from django.views.decorators.http import require_http_methods

from django.views.decorators.csrf import csrf_protect

from common.utils import http_response_json
from accounts.decorators import login_required
import logging
from ..models import AccessLog
from datetime import datetime

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
    post_data = json.loads(request.body)
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
