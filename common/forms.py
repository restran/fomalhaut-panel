# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

import logging
import traceback

from django import forms

logger = logging.getLogger(__name__)


class BaseModelForm(forms.ModelForm):
    """
    """
    # class Meta:
    # model = MonitorGroup
    # fields = ()

    @classmethod
    def get_default_form_json(cls, monitor_group=None):
        """
        获取缺省表单数据
        :return:
        """
        d = cls.Meta.model()
        j = {}
        for t in cls.Meta.fields:
            try:
                # many-to-many 需要 d 已保存到数据库中
                v = getattr(d, t)
            except ValueError:
                v = ''
            except Exception:
                v = ''

            # 如果是None，就用''
            data = v if v is not None else ''
            j[t] = {'data': data, 'has_error': False, 'errors': ''}

        logger.debug(j)
        return j

    def get_form_json(self):
        """
        获取缺省表单数据
        :return:
        """
        j = {}
        for t in self.Meta.fields:
            v = self[t]
            j[t] = {'data': v.data, 'has_error': len(v.errors) > 0, 'errors': ', '.join(v.errors)}
        logger.debug('get_form_json')
        logger.debug(j)
        return j
