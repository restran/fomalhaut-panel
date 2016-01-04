# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
import logging
import traceback

from django import forms
from django.utils.translation import ugettext_lazy as _

from .models import SiteUser
from .utils import authenticate
from . import utils

logger = logging.getLogger(__name__)


class UserInfoEditForm(forms.ModelForm):
    """
    用户修改个人信息的表单
    """

    def __init__(self, user_id, *args, **kwargs):
        super(UserInfoEditForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
        self.error_msg = []

    class Meta:
        model = SiteUser
        fields = ("name", "email",)

    def clean_email(self):
        logger.debug('UserInfoEditForm clean_email')
        email = self.cleaned_data["email"]
        cnt = SiteUser.objects.filter(email=email).exclude(id=self.user_id).count()
        if cnt <= 0:
            return email
        else:
            self.error_msg.append('该邮箱已存在')
            raise forms.ValidationError(_("该邮箱已存在"))


class UserInfoCreateForm(forms.ModelForm):
    """
    用户提交注册的表单，用来创建用户
    """

    def __init__(self, *args, **kwargs):
        super(UserInfoCreateForm, self).__init__(*args, **kwargs)
        self.error_msg = []

    class Meta:
        model = SiteUser
        fields = ("name", "email")

    # clean 函数会按fields字段顺序自动执行
    def clean_email(self):
        email = self.cleaned_data["email"]
        count = SiteUser.objects.filter(email=email).count()
        if count <= 0:
            return email

        self.error_msg.append('该邮箱已存在')
        raise forms.ValidationError(_("该邮箱已存在"))

    def save(self, commit=True, is_admin=False):
        user = super(UserInfoCreateForm, self).save(commit=False)
        if is_admin:
            user.is_admin = True
        if commit:
            user.save()
            try:
                utils.send_user_creation_email(user)
                pass
            except Exception, e:
                logger.error(e.message)
                logger.error(traceback.format_exc())
                return False, '创建用户出现异常', None
        return True, '', user


class UserCreationForm(forms.ModelForm):
    """
    用户提交注册的表单，用来创建用户
    """

    class Meta:
        model = SiteUser
        fields = ("name", "email", "password")

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            SiteUser.objects.get(email=email)
        except SiteUser.DoesNotExist:
            return email

        raise forms.ValidationError(_("该邮箱已存在"))

    def save(self, commit=True, is_admin=False):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if is_admin:
            user.is_active = True  # 管理员创建后就是激活状态
            user.is_admin = True
        if commit:
            user.save()
        return user


class AuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    email/password logins.
    """
    email = forms.EmailField(label=_("email"))
    password = forms.CharField(label=_("password"), widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = authenticate(email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    _("Please enter a correct username and password. Note that both fields are case-sensitive."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))

        # TODO: determine whether this should move to its own method.
        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(
                    _("Your Web browser doesn't appear to have cookies enabled. Cookies are required for logging in."))

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class PasswordResetForm(forms.Form):
    """
    申请重置密码
    """
    email = forms.EmailField(label=_("email"),
                             error_messages={'required': _("这个是必填项"),
                                             'invalid': _("请输入正确的邮箱")})

    def __init__(self, *args, **kwargs):
        self.user = None
        super(PasswordResetForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        logger.debug('clean_email')
        email = self.cleaned_data["email"]
        try:
            self.user = SiteUser.objects.get(email=email)
            return email
        except SiteUser.DoesNotExist:
            raise forms.ValidationError(_("该邮箱不存在"))

    def save(self):
        """
        Generates a one-use only link for resetting password and sends to the user
        """
        utils.send_password_reset_email(self.user)


class PasswordChangeForm(forms.Form):
    """
    输入旧密码来修改密码
    """
    old_password = forms.CharField(widget=forms.PasswordInput,
                                   error_messages={'required': _("这个是必填项")})
    new_password = forms.CharField(widget=forms.PasswordInput,
                                   error_messages={'required': _("这个是必填项")})

    def __init__(self, user, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.user = user
        self.error_msg = []

    def clean_old_password(self):
        """
        Validates that the old_password field is correct.
        """

        # 当old_password已经校验出错时，self.cleaned_data中是没有old_password
        old_password = self.cleaned_data.get("old_password", None)
        if old_password and not self.user.check_password(old_password):
            self.error_msg.append("旧密码不正确")
            raise forms.ValidationError(_("旧密码不正确"))

        return old_password

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password'])
        # 创建用户后，用户重置了密码，就是激活该用户
        self.user.is_active = True
        if commit:
            self.user.save()
        return self.user
