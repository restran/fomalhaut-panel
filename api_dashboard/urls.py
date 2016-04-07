# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

from django.conf.urls import url
from django.conf.urls.static import static

from api_dashboard import settings
from accounts.urls import urlpatterns as accounts_urls
from dashboard.urls import urlpatterns as dashboard_urls
from common.utils import error_404

# accounts的urls
urlpatterns = []
urlpatterns.extend(accounts_urls)
urlpatterns.extend(dashboard_urls)

# 仅供DEBUG=True时使用
urlpatterns.extend(
    static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS)
)

urlpatterns.extend([
    url(r'^', error_404)
])
