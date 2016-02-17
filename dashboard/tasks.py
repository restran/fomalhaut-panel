# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals
import json

import traceback

from datetime import datetime

import redis

from models import *
from api_dashboard import settings
from api_dashboard.celery import app

logger = logging.getLogger(__name__)


@app.task
def clear_old_access_logs():
    """
    清理过期的访问日志数据
    :return:
    """
    logger.info('执行 clear_old_access_logs')
    access_log_keep_days = settings.ACCESS_LOG_KEEP_DAYS
    expires = datetime.datetime.utcnow() - datetime.timedelta(days=access_log_keep_days)
    logger.debug(expires)

    AccessLog.objects.filter(time__lt=expires).delete()

    logger.info('执行 clear_old_access_logs 完成')


@app.task
def parse_access_logs():
    """
    解析访问日志数据
    :return:
    """
    success = True
    logger.info('执行 parse_access_logs')
    try:
        r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                              db=settings.REDIS_DB, password=settings.REDIS_PASSWORD)

        # 获取所有统计分析日志，并从redis中删除
        pattern_get_and_delete_lua = """
        local keys = redis.call('keys', ARGV[1])
        local values = {}
        for i = 1, table.getn(keys) do
            values[i] = redis.call('get', keys[i])
            redis.call('del', keys[i])
        end
        return values
        """
        lua = r.register_script(pattern_get_and_delete_lua)
        logs = lua(keys=[''], args=['%s:*' % settings.ANALYTICS_REDIS_PREFIX], client=r)
        logger.debug(logs)

        # access_ip_counter_dict = {}
        access_day_counter_dict = {}
        access_day_pv_counter_dict = {}
        access_log_list = []
        for t in logs:
            # redis 中存储的是json字符串
            t = json.loads(t)
            access_log = AccessLog()
            access_log.result_code = t.get('result_code', ACCESS_RESULT_UNKNOWN)
            access_log.url = t.get('url')
            access_log.agent_id = t.get('agent_id')
            access_log.site_id = t.get('site_id')
            access_log.agent_name = t.get('agent_name', '')
            access_log.site_name = t.get('site_name', '')
            access_log.remote_ip = t.get('remote_ip', '')
            access_log.status_code = t.get('status_code')
            access_log.method = t.get('method', 'GET')
            access_log.header_token = t.get('header_token', False)
            access_log.elapsed = t.get('elapsed', -1)
            try:
                access_log.time = datetime.strptime(t.get('time'), '%Y-%m-%d %H:%M:%S:%f')
            except Exception as e:
                logger.error(u'datetime 转换出错, %s' % t.get('time'))
                access_log.time = datetime.now()

            access_log.date = access_log.time.date()
            access_log.hour = access_log.time.hour
            access_log_list.append(access_log)

            # 按日期计算访问量
            key = access_log.date.strftime('%Y-%m-%d')
            if access_log.header_token:
                date_counter = access_day_pv_counter_dict.get(key)
                if date_counter:
                    date_counter.count += 1
                else:
                    date_counter = AccessDayCounter()
                    date_counter.date = access_log.date
                    date_counter.count = 1
                    date_counter.page_view = True
                    access_day_pv_counter_dict[key] = date_counter
            else:
                date_counter = access_day_counter_dict.get(key)
                if date_counter:
                    date_counter.count += 1
                else:
                    date_counter = AccessDayCounter()
                    date_counter.date = access_log.date
                    date_counter.count = 1
                    date_counter.page_view = False
                    access_day_counter_dict[key] = date_counter

                    # 计算IP访问量
                    # ip_date_counter_dict = access_ip_counter_dict.get(key)
                    # if ip_date_counter_dict is None:
                    #     ip_date_counter_dict = {}
                    #     access_ip_counter_dict[key] = ip_date_counter_dict
                    #
                    # ip_counter = ip_date_counter_dict.get(access_log.remote_ip)
                    # if ip_counter:
                    #     ip_counter.count += 1
                    # else:
                    #     ip_counter = AccessIPCounter()
                    #     ip_counter.date = access_log.date
                    #     ip_counter.count = 1
                    #     ip_counter.remote_ip = access_log.remote_ip
                    #     ip_counter[access_log.remote_ip] = ip_counter

        AccessLog.objects.bulk_create(access_log_list, batch_size=2000)

        access_day_counter_list = []
        access_day_counter_list.extend(access_day_counter_dict.values())
        access_day_counter_list.extend(access_day_pv_counter_dict.values())

        # access_ip_counter_list = []
        # for t in access_ip_counter_dict.values():
        #     access_ip_counter_list.extend(t.values())

        for t in access_day_counter_list:
            try:
                adc = AccessDayCounter.objects.get(date=t.date, page_view=t.page_view)
                adc.count += t.count
                adc.save()
            except AccessDayCounter.DoesNotExist as e:
                t.save()
            except AccessDayCounter.MultipleObjectsReturned as e:
                logger.error(e.message)
                logger.error(traceback.format_exc())
                logger.error('不应该出现这个问题')

                # for t in access_ip_counter_list:
                #     try:
                #         aic = AccessIPCounter.objects.get(date=t.date, remote_ip=t.remote_ip)
                #         aic.count += t.count
                #         aic.save()
                #     except AccessDayCounter.DoesNotExist as e:
                #         t.save()
                #     except AccessDayCounter.MultipleObjectsReturned as e:
                #         logger.error(e.message)
                #         logger.error(traceback.format_exc())
                #         logger.error(u'不应该出现这个问题')

    except Exception as e:
        logger.error('执行 parse_access_logs 出现异常')
        logger.error(e.message)
        logger.error(traceback.format_exc())
        success = False

    logger.info('执行 parse_access_logs 完成')

    return success
