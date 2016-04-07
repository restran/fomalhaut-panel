# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

import logging

from .utils import get_user
from .settings import SITE_NAME

logger = logging.getLogger(__file__)


class LazyUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_site_cached_user'):
            request._site_cached_user = get_user(request)
        logger.debug('LazyUser get')
        logger.debug(request._site_cached_user)
        return request._site_cached_user


class AuthenticationMiddleware(object):
    @staticmethod
    def process_request(request):
        request.site_name = SITE_NAME
        logger.debug('process_request')
        assert hasattr(request, 'session')  # 需要安装session中间件
        request.__class__.site_user = LazyUser()
        return None
