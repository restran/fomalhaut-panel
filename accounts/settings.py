# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

# 从settings 中导入需要用到的设置
from api_dashboard.settings import SITE_NAME, \
    SITE_DOMAIN, \
    EMAIL_NOTIFY_NAME, \
    EMAIL_SMTP_SERVER

# 密码重置链接的有效时间
PASSWORD_RESET_TIMEOUT_DAYS = 1

# 登陆选择多少天后过期，修改了这里也要相应修改login.html
LOGIN_EXPIRY_DAY = 365
