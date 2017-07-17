# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from common.utils import error_404, http_response_json, json_loads
from . import settings
from .decorators import login_required, admin_required
from .forms import *
from .tokens import PasswordResetTokenGenerator
from .utils import login


@csrf_protect
@require_http_methods(["POST"])
def api_create_admin(request):
    """
    网站刚开始运行时，没有管理员，需要创建一个
    :param request:
    :return:
    """
    logger.debug('api_create_admin')
    msg, success, data = '', False, []
    if SiteUser.has_admin():
        return error_404(request)
    else:
        logger.debug(request.body)
        post_data = json_loads(request.body)
        form = UserCreationForm(post_data)
        if form.is_valid():
            form.save(is_admin=True)  # 将数据保存到数据库中
            success = True

        response = {'success': success, 'msg': msg, 'data': data}
        logger.debug(data)
        return http_response_json(response)


@csrf_protect
@require_http_methods(["POST"])
def api_user_login(request):
    """
    用户登录
    :param request:
    :return:
    """
    logger.debug('api_user_login')
    msg, success = '', False
    if not SiteUser.has_admin():
        # 如果还没有创建管理员，就先创建管理员
        return http_response_json({'success': False, 'msg': '请先创建管理员'})
    else:
        post_data = json_loads(request.body)
        email = post_data.get('email', '')
        password = post_data.get('password', '')
        remember_me = post_data.get('remember_me', False)
        if remember_me:
            # 不使用datetime的原因是会涉及到时区的问题，太麻烦，未解决
            expiry = 3600 * 24 * settings.LOGIN_EXPIRY_DAY
            # N天后到期
        else:
            expiry = 0  # 关闭浏览器后到期

        user = authenticate(email=email, password=password)
        logger.debug(user)
        if user is not None:
            logger.debug('认证通过')
            # 认证通过
            login(request, user, expiry)
            # 跳转到登陆成功的页面
            logger.debug('跳转到主页')
            return http_response_json({'success': True, 'msg': '', 'redirect_uri': '/'})
        else:
            logger.debug('认证失败')
            response = {'success': False, 'msg': '登录失败，邮箱或密码不正确'}
            return http_response_json(response)


@admin_required
@csrf_protect
@require_http_methods(["GET"])
def api_get_accounts(request):
    """
    获取所有用户
    :param request:
    :return:
    """
    logger.debug('api_get_accounts')
    data = SiteUser.get_all_in_json()
    response = {'success': True, 'msg': '', 'data': data}
    return http_response_json(response)


@admin_required
@csrf_protect
@require_http_methods(["POST"])
def api_create_account(request):
    """
    创建用户基本信息
    :param request:
    :return:
    """
    msg, success = '', False
    logger.debug('api_create_account')
    post_data = json_loads(request.body)
    logger.debug(post_data)
    form = UserInfoCreateForm(post_data)
    if form.is_valid():
        success, msg, user = form.save()  # 将数据保存到数据库中

        response = {'success': success, 'msg': msg}
        if success:
            response['item'] = user.to_json_dict()
        return http_response_json(response)
    else:
        logger.debug(form.error_msg)
        return http_response_json({'success': success, 'msg': ', '.join(form.error_msg)})


@admin_required
@csrf_protect
@require_http_methods(["POST"])
def api_update_account(request, user_id):
    """
    更新用户基本信息
    :param request:
    :param user_id:
    :return:
    """
    msg, success = '', False
    logger.debug('api_update_account')
    logger.debug(request.POST)
    post_data = json_loads(request.body)
    user = SiteUser.get_user(user_id)
    if user is None:
        return http_response_json({'success': success, 'msg': '用户不存在'})

    form = UserInfoEditForm(post_data, instance=user)
    if form.is_valid():
        logger.debug('is_valid')
        user.name = form.cleaned_data["name"]
        user.email = form.cleaned_data["email"]
        user.save()
        return http_response_json({'success': True, 'msg': ''})
    else:
        return http_response_json({'success': False, 'msg': ', '.join(form.error_msg)})


@admin_required
@csrf_protect
@require_http_methods(["POST"])
def api_delete_account(request):
    """
    删除用户
    :param request:
    :return:
    """
    msg, success = '', False
    logger.debug('api_delete_account')
    post_data = json_loads(request.body)
    user_id = post_data.get('user_id', None)
    if user_id:
        try:
            if SiteUser.delete_user(user_id):
                success = True
        except Exception as e:
            logger.debug(e)
            msg = '删除用户出现异常'

    return http_response_json({'success': success, 'msg': msg})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_update_password(request):
    """
    更新密码
    :param request:
    :return:
    """
    msg, success = '', False
    logger.debug('api_update_password')
    post_data = json_loads(request.body)
    if hasattr(request, 'site_user'):
        user = request.site_user
        form = PasswordChangeForm(user, post_data)
        if form.is_valid():
            form.save()
            success = True
        else:
            msg = ', '.join(form.error_msg)
    else:
        msg = '用户不存在'

    return http_response_json({'success': success, 'msg': msg})


@csrf_protect
@require_http_methods(["POST"])
def api_reset_password(request):
    """
    通过邮箱重置密码
    :param request:
    :return:
    """
    msg, success = '', False
    logger.debug('api_reset_password')
    post_data = json_loads(request.body)
    user_id = post_data.get('user_id', None)
    token = post_data.get('token', None)
    new_password = post_data.get('new_password', None)
    if not (user_id and token and new_password):
        return http_response_json({'success': False, 'msg': '非法请求'})

    user = SiteUser.get_user(user_id)

    if user is None:
        return http_response_json({'success': False, 'msg': '非法请求'})

    token_generator = PasswordResetTokenGenerator()
    check_result = token_generator.check_token(user, token)
    if not check_result:
        return http_response_json({'success': False, 'msg': '非法请求'})

    user.set_password(new_password)
    user.save()
    success = True

    return http_response_json({'success': success, 'msg': msg})


@csrf_protect
@require_http_methods(["POST"])
def reset_password_request(request):
    """
    通过邮箱申请重置密码
    :param request:
    :return:
    """
    msg, success = '', False
    logger.debug('api_reset_password')
    post_data = json_loads(request.body)
    form = PasswordResetForm(post_data)
    if form.is_valid():
        logger.debug('form is valid')
        form.save()
        success = True
    else:
        errors = form.errors.values()
        msg = [t2 for t1 in errors for t2 in t1]
    return http_response_json({'success': success, 'msg': msg})
