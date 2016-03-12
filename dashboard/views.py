# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
import re

import traceback
from datetime import datetime

from django.utils.encoding import smart_str, smart_unicode
from django.utils.http import urlquote
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from django.template import RequestContext

from forms import *
from accounts.decorators import login_required
from common.utils import error_404, json_dumps

logger = logging.getLogger(__name__)


def index(request):
    return render_to_response(
        'dashboard.html', {'request': request},
        context_instance=RequestContext(request))


def test(request):
    from dashboard.tasks import parse_access_logs
    from dashboard.models import AccessLog
    # AccessLog.objects().update(flag=False)
    parse_access_logs()
    # pipeline = [
    #     {"$group": {"_id": "$date", "count": {"$sum": 1}}}
    # ]
    # ret = AccessHourCounter.objects().aggregate(*pipeline)
    # pipeline = [
    #     {"$group": {"_id": {"date": "$date", "client_id": "$client_id"}, "count": {"$sum": 1}}}
    # ]
    # ret = AccessHourCounter.objects().aggregate(*pipeline)
    # logger.debug(ret)
    return HttpResponse("test")


@login_required
@ensure_csrf_cookie
def dashboard(request):
    request.page_title = '仪表盘'
    request.current_page = 'dashboard'
    return render_to_response('dashboard.html', {'request': request})


@login_required
@ensure_csrf_cookie
def access_log(request):
    request.page_title = '访问日志'
    request.current_page = 'access_log'

    return render_to_response('dashboard/access_log.html', {'request': request})


def help_page(request, page_name):
    request.page_title = page_name

    try:
        return render_to_response("dashboard/help/" + page_name.replace('-', '_').lower() + ".html",
                                  {'request': request})
    except Exception as e:
        logger.error(e.message)
        return error_404(request)


# 如果html页面的表单中没有{%csrftoken%}，
# django 就不会自动设置csrf token的cookie
# 需要ensure_csrf_cookie，来强制添加
@login_required
@ensure_csrf_cookie
def config(request, data_type='client'):
    """
    配置
    :param request:
    :return:
    """
    if data_type == 'client':
        request.page_title = '应用配置'
        display_breadcrumb = True
    elif data_type == 'endpoint':
        request.page_title = 'API 端点'
        display_breadcrumb = False
    elif data_type == 'client_endpoint':
        request.page_title = '应用配置'
        display_breadcrumb = True
    elif data_type == 'import-export':
        request.page_title = '导入导出'
        display_breadcrumb = False
    else:
        return error_404(request)

    request.current_page = 'config'

    config_info = {
        'data_type': data_type,
        'display_breadcrumb': display_breadcrumb,
        'client_id': None,
        'client_name': None
    }

    client_id = request.GET.get('client_id')
    if client_id:
        client = Client.get_client(client_id)
        if client:
            config_info['client_id'] = client.id
            config_info['client_name'] = client.name

    logger.debug(config_info)
    return render_to_response('dashboard/config.html',
                              {'request': request, 'config_info': config_info})


@login_required
@ensure_csrf_cookie
def config_client(request):
    """
    client 配置
    :param request:
    :return:
    """
    request.page_title = '代理配置'
    request.current_page = 'proxy_config'

    # 管理的数据类型，monitor_group 表示监控组
    data_type = request.GET.get('data_type', 'access_agent')

    config_info = {'data_type': data_type, 'display_breadcrumb': True}

    agent_id = request.GET.get('agent_id')
    if agent_id:
        agent = Client.get_client(agent_id)
        if agent:
            config_info['agent_id'] = agent.id
            config_info['agent_name'] = agent.name

    logger.debug(config_info)

    return render_to_response('dashboard/config.html',
                              {'request': request, 'config_info': config_info})


@login_required
def export_config(request):
    """
    导出配置
    :param request:
    :return:
    """
    try:
        file_name = 'export_config_%s.json' % datetime.today().strftime('%Y%m%d')
        json_data = get_export_config_json()
        config_data = json_dumps(json_data, indent=4, sort_keys=True)

        agent = request.META.get('HTTP_USER_AGENT')
        if agent and re.search('MSIE', agent):
            # 解决ie不能下载的问题
            response = HttpResponse(content=config_data, content_type="text/plain; charset=utf-8")
            # 解决文件名乱码/不显示的问题
            response['Content-Disposition'] = 'attachment; filename=%s' % urlquote(file_name)
        else:
            response = HttpResponse(content=config_data, content_type="text/plain; charset=utf-8")
            response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file_name)

        return response
    except Exception as e:
        logger.error(e.message)
        logger.error(traceback.format_exc())
        return HttpResponse('导出配置失败 %s' % e.message)
