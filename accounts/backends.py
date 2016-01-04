# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

from models import SiteUser


class EmailAuthBackend(object):
    """
    Email Authentication Backend
    
    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    """

    def authenticate(self, email=None, password=None):
        """ Authenticate a user based on email address as the user name. """
        try:
            user = SiteUser.objects.get(email=email)
            if user.check_password(password):
                return user
        except SiteUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        """ Get a User object from the user_id. """
        try:
            user = SiteUser.objects.get(pk=user_id)
            # user.last_login = datetime.datetime.now()  # 用户上线
            # user.save(update_fields=['last_login'])  # 将数据写入数据库
        except SiteUser.DoesNotExist:
            return None
        else:
            return user
