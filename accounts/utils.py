# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

from .settings import *
from common.tasks import send_mail_by_postfix
import datetime
from warnings import warn
import logging

from django.core.exceptions import ImproperlyConfigured
from importlib import import_module

from .tokens import default_token_generator
from .backends import EmailAuthBackend
from .models import AnonymousUser

logger = logging.getLogger(__file__)
SESSION_KEY = 'auth_user_id'
BACKEND_SESSION_KEY = 'auth_user_backend'
REDIRECT_FIELD_NAME = 'next'


def load_backend(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i + 1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing authentication backend %s: "%s"' % (path, e))
    except ValueError as e:
        raise ImproperlyConfigured(
            'Error importing authentication backends. Is AUTHENTICATION_BACKENDS a correctly defined list or tuple?')
    try:
        cls = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" authentication backend' % (module, attr))
    try:
        getattr(cls, 'supports_object_permissions')
    except AttributeError:
        warn(
            "Authentication backends without a `supports_object_permissions` attribute are deprecated. Please define it in %s." % cls,
            PendingDeprecationWarning)
        cls.supports_object_permissions = False
    try:
        getattr(cls, 'supports_anonymous_user')
    except AttributeError:
        warn(
            "Authentication backends without a `supports_anonymous_user` attribute are deprecated. Please define it in %s." % cls,
            PendingDeprecationWarning)
        cls.supports_anonymous_user = False
    return cls()


def authenticate(**credentials):
    """
    If the given credentials are valid, return a User object.
    """
    backend = EmailAuthBackend()

    try:
        user = backend.authenticate(**credentials)
    except TypeError:
        # This backend doesn't accept these credentials as arguments.
        user = None
    if user is not None:
        # Annotate the user object with the path of the backend.
        user.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
        return user


def login(request, user, expiry):
    """
    Persist a user id and a backend in the request. This way a user doesn't
    have to reauthenticate on every request.
    """
    if user is None:
        user = request.site_user
    # TODO: It would be nice to support different login methods, like signed cookies.
    user.last_login = datetime.datetime.now()  # 更新上次登陆时间
    user.save()  # 将数据写入数据库

    if SESSION_KEY in request.session:
        if request.session[SESSION_KEY] != user.id:
            # To avoid reusing another user's session, create a new, empty
            # session if the existing session corresponds to a different
            # authenticated user.
            request.session.flush()
    else:
        request.session.cycle_key()
    request.session[SESSION_KEY] = user.id
    request.session[BACKEND_SESSION_KEY] = user.backend
    request.session.set_expiry(expiry)
    # expiry如果是整数，则表示多少秒后到期
    # 如果是datetime，则在该datetime到达时到期
    # 如果是0，则表示关闭浏览器后到期
    # 如果是None，则采用默认的过期时间
    if hasattr(request, 'site_user'):
        request.site_user = user


def logout(request):
    """
    Removes the authenticated user's ID from the request and flushes their
    session data.
    """
    request.session.flush()
    if hasattr(request, 'site_user'):
        request.site_user = AnonymousUser()


def get_user(request):
    logger.debug('run get_user')
    try:
        logger.debug(SESSION_KEY)
        user_id = request.session[SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
        backend = load_backend(backend_path)
        user = backend.get_user(user_id) or AnonymousUser()
    except KeyError:
        user = AnonymousUser()
    return user


def send_email(user, title, message, email_template_name, token_generator=default_token_generator):
    from django.template import Context, loader

    context = {
        'email': user.email,
        'domain': SITE_DOMAIN,
        'site_name': SITE_NAME,
        'message': message,
        'expire_time': str(PASSWORD_RESET_TIMEOUT_DAYS * 24) + '小时',
        'user': user,
        'token': token_generator.make_token(user),
        'protocol': 'http',
    }
    # email_template_name = 'account/reset_password_email.html'
    t = loader.get_template(email_template_name)
    mail_to_list = [user.name + ' <' + user.email + '>', ]

    # 使用 celery 异步发送
    send_mail_by_postfix.delay(mail_to_list, 'plain', t.render(Context(context)), title)


def send_password_reset_email(user):
    logger.debug('run send_password_reset_email')
    send_email(user=user, title=u'来自 ' + SITE_NAME + ' 的密码重置',
               message='你申请了密码重置',
               email_template_name='accounts/password_reset_email.html')
    logger.debug('邮件发送请求已提交')


def send_user_creation_email(user):
    logger.debug('run send_user_creation_email')
    send_email(user=user, title=u'来自 ' + SITE_NAME + ' 的用户创建',
               message='你的账号已创建',
               email_template_name='accounts/password_reset_email.html')
    logger.debug('邮件发送请求已提交')
