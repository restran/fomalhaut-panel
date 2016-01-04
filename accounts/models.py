# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

import hashlib
from django.db import models
from django.utils.encoding import smart_str
from common.utils import datetime_to_str


class AnonymousUser(object):
    def __init__(self):
        pass

    def __unicode__(self):
        return 'AnonymousUser'

    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False


UNUSABLE_PASSWORD = '!'  # This will never be a valid hash


def get_hexdigest(algorithm, salt, raw_password):
    """
    Returns a string of the hexdigest of the given plaintext password and salt
    using the given algorithm ('md5', 'sha1' or 'crypt').
    """
    raw_password, salt = smart_str(raw_password), smart_str(salt)
    if algorithm == 'crypt':
        try:
            import crypt
        except ImportError:
            raise ValueError('"crypt" password algorithm not supported in this environment')
        return crypt.crypt(raw_password, salt)

    if algorithm == 'md5':
        return hashlib.md5(salt + raw_password).hexdigest()
    elif algorithm == 'sha1':
        return hashlib.sha1(salt + raw_password).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(salt + raw_password).hexdigest()
    raise ValueError("Got unknown password algorithm type in password.")


def check_password(raw_password, enc_password):
    """
    Returns a boolean of whether the raw_password was correct. Handles
    encryption formats behind the scenes.
    """
    algo, salt, hsh = enc_password.split('$')
    return hsh == get_hexdigest(algo, salt, raw_password)


class SiteUser(models.Model):
    """
    用户的模型
    name, email and password are required. Other fields are optional.
    """
    name = models.CharField(max_length=14)
    email = models.EmailField(unique=True)
    # 当用户没有激活的时候，就没有密码
    password = models.CharField(max_length=128, blank=True)
    # "Use '[algo]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."
    last_login = models.DateTimeField(null=True)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)  # 是否是管理员
    is_active = models.BooleanField(default=False)  # 用户是否激活

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        app_label = 'accounts'

    @classmethod
    def has_admin(cls):
        """
        判断是否有管理员账号
        """
        if SiteUser.objects.filter(is_admin=True).count() <= 0:
            return False
        else:
            return True

    @classmethod
    def get_user(cls, user_id):
        """
        获取用户
        """
        try:
            return SiteUser.objects.get(id=user_id)
        except SiteUser.DoesNotExist:
            return None

    @classmethod
    def delete_user(cls, user_id):
        """
        删除用户
        """
        try:
            SiteUser.objects.get(id=user_id).delete()
            return True
        except SiteUser.DoesNotExist:
            return False

    def to_json_dict(self):
        d = {'id': self.id, 'email': self.email, 'name': self.name,
             'last_login': datetime_to_str(self.last_login),
             'date_joined': datetime_to_str(self.date_joined),
             'is_active': self.is_active, 'is_admin': self.is_admin}

        return d

    @classmethod
    def get_all_in_json(cls):
        """
        获取所有用户的信息
        """
        users = SiteUser.objects.all().order_by('date_joined')
        json_list = []
        for t in users:
            json_list.append(t.to_json_dict())

        return json_list

    @classmethod
    def get_users(cls):
        """
        获取所有用户的信息
        """
        return SiteUser.objects.all()

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def get_name(self):
        return self.name

    def set_password(self, raw_password):
        if raw_password is None:
            self.set_unusable_password()
        else:
            import random

            algo = 'sha256'
            salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:32]
            hsh = get_hexdigest(algo, salt, raw_password)
            self.password = '%s$%s$%s' % (algo, salt, hsh)

    def check_password(self, raw_password):
        """
        Returns a boolean of whether the raw_password was correct. Handles
        encryption formats behind the scenes.
        """
        # Backwards-compatibility check. Older passwords won't include the
        # algorithm or salt.
        if '$' not in self.password:
            is_correct = (self.password == get_hexdigest('sha256', '', raw_password))
            if is_correct:
                # Convert the password to the new, more secure format.
                self.set_password(raw_password)
                self.save()
            return is_correct
        return check_password(raw_password, self.password)

    def set_unusable_password(self):
        # Sets a value that will never be a valid hash
        self.password = UNUSABLE_PASSWORD

    def has_usable_password(self):
        if self.password is None \
                or self.password == UNUSABLE_PASSWORD:
            return False
        else:
            return True
