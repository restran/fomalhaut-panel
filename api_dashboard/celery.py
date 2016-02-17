# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
from __future__ import absolute_import

import os
from celery import Celery, platforms
from django.conf import settings


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_dashboard.settings')

app = Celery('api_dashboard')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
    # 当序列化的内容格式为pickle时
    # 当以 root 用户运行 celery worker 时，会出现
    # Running a worker with superuser privileges when the
    # worker accepts messages serialized with pickle is a very bad idea!
    # If you really want to continue then you have to set the C_FORCE_ROOT
    # environment variable (but please think about this before you do).

    # 但是如果设置为json时，有些任务的参数传递的是类对象，会出现无法序列化成json

    # 这里全部设置为json，默认是pickle
    # CELERY_TASK_SERIALIZER='json',
    # 默认情况下，在生产环境是拒绝 pickle，必须手动设置才可以使用
    # 因为 Pickle 可能会导致攻击的问题
    CELERY_ACCEPT_CONTENT=['pickle', 'json', 'msgpack', 'yaml']
    # CELERY_RESULT_SERIALIZER='json',
)

# 加上这一行就不会出现
# Running a worker with superuser privileges when the
# worker accepts messages serialized with pickle is a very bad idea!
platforms.C_FORCE_ROOT = True
