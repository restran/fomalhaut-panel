# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.template import RequestContext

from .tokens import PasswordResetTokenGenerator
from .forms import *
from .models import *
from .decorators import login_required, admin_required
from .utils import logout
from common.utils import error_404

import logging

logger = logging.getLogger(__name__)


@ensure_csrf_cookie
def create_admin(request):
    """
    网站刚开始运行时，没有管理员，需要创建一个
    :param request:
    :return:
    """
    if SiteUser.has_admin():
        return error_404(request)
    else:
        request.page_title = '创建管理员'
        return render_to_response('accounts/create_admin.html', {'request': request})
        # 使用 context_instance=RequestContext(request) 会出现问题
        # Model class django.contrib.auth.models. Permission doesn't declare an explicit app_label and either
        # isn't in an application in INSTALLED_APPS or else was imported before its application was loaded.
        # return render_to_response('accounts/create_admin.html', {'request': request},
        #                            context_instance=RequestContext(request))
        # 解决csrf_protect不能工作，在前端不能显示csrf_token
        # 加上context_instance=RequestContext(request)


@ensure_csrf_cookie
def user_login(request):
    """
    用户登录
    :param request:
    :return:
    """
    logger.info('user_login')
    if not SiteUser.has_admin():
        # 如果还没有创建管理员，就先创建管理员
        return HttpResponseRedirect('/accounts/create_admin/')
    else:
        # 如果已登陆则跳转到主页
        if hasattr(request, 'site_user') and \
                request.site_user.is_authenticated():
            return HttpResponseRedirect('/')

        request.page_title = '登录'
        return render_to_response('accounts/login.html', {'request': request})


@login_required
def user_logout(request):
    """
    退出登录
    :param request:
    :return:
    """
    logout(request)
    return HttpResponseRedirect('/')  # 跳转到主页


@admin_required
@ensure_csrf_cookie
def manage_accounts(request):
    """
    管理账户
    :param request:
    :return:
    """
    request.page_title = '用户管理'
    request.current_page = 'accounts'
    entries = SiteUser.get_users()
    return render_to_response('accounts/manage_accounts.html',
                              {'request': request, 'entries': entries})


@login_required
@ensure_csrf_cookie
def account_profile(request):
    """
    个人信息查看页面，也是密码修改页面
    :param request:
    :return:
    """

    request.page_title = '个人信息'
    request.current_page = 'accounts'
    if hasattr(request, 'site_user'):
        user = request.site_user
    else:
        return error_404(request)

    return render_to_response('accounts/profile.html',
                              {'request': request,
                               'user': user})


@ensure_csrf_cookie
def password_reset_request(request):
    """
    密码重置申请
    :param request:
    :return:
    """
    request.page_title = '申请重置密码'
    return render_to_response('accounts/password_reset_request.html',
                              {'request': request})


@ensure_csrf_cookie
def password_reset_confirm(request, user_id, token):
    """
    密码重置页面
    :param request:
    :param user_id:
    :param token:
    :return:
    """
    request.page_title = '重置密码'
    try:
        user = SiteUser.objects.get(id=user_id)
        token_generator = PasswordResetTokenGenerator()
        check_result = token_generator.check_token(user, token)
        request.token = token
        if check_result:
            return render_to_response('accounts/password_reset_confirm.html',
                                      {'request': request,
                                       'user': user,
                                       'check_result': check_result})
    except SiteUser.DoesNotExist:
        return error_404(request)
