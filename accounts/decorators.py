# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
import logging

from django.http import HttpResponseRedirect

from common.utils import error_404
from common.utils import http_response_json

__author__ = 'restran'

logger = logging.getLogger(__name__)


def login_required(view):
    """
    判断需要登陆的装饰器
    :param view:
    :return:
    """

    def decorator(request, *args, **kwargs):
        if request.site_user.is_authenticated():
            return view(request, *args, **kwargs)
        else:
            logger.debug('跳转到登录页')

        # 如果是通过API调用的方法，则返回错误信息，而不是跳转到登录页面
        content_type = request.META.get('CONTENT_TYPE', '').lower()
        http_accept = request.META.get('HTTP_ACCEPT', '').lower()
        if content_type.startswith("application/json") \
                or 'application/json' in http_accept:
            return http_response_json({'success': False, 'msg': '登录会话已超时，请刷新页面重新登录'})

        return HttpResponseRedirect('/accounts/login/')

    return decorator


def admin_required(view):
    """
    判断需要登陆的装饰器
    :param view:
    :return:
    """

    def decorator(request, *args, **kwargs):
        if request.site_user.is_authenticated() and request.site_user.is_admin:
            return view(request, *args, **kwargs)
        else:
            # 如果是通过API调用的方法，则返回错误信息，而不是跳转到登录页面
            content_type = request.META.get('CONTENT_TYPE', '').lower()
            http_accept = request.META.get('HTTP_ACCEPT', '').lower()
            if content_type.startswith("application/json") \
                    or 'application/json' in http_accept:
                return http_response_json({'success': False, 'msg': '登录会话已超时，请刷新页面重新登录'})

            return error_404(request)

    return decorator
