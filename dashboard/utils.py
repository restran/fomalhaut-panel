# -*- coding: utf-8 -*-
# created by restran on 2016/04/14
from __future__ import unicode_literals, absolute_import
import redis
from fomalhaut import settings

_get_next_log_lua = """
local key
local value
while (1)
do
    key = redis.call('lpop', KEYS[1])
    if key then
        value = redis.call('get', key)
        if value then
            redis.call('del', key)
            return value
        end
    else
        return nil
    end
end
"""


class RedisHelper(object):
    """
    redis 连接助手
    """
    _client = None
    _next_log_lua = None

    def __init__(self):
        if RedisHelper._client is None:
            self._create_redis_client()

    @classmethod
    def get_client(cls):
        if RedisHelper._client is None:
            cls._create_redis_client()

        return RedisHelper._client

    @classmethod
    def get_next_log(cls, log_key=settings.ANALYTICS_LOG_REDIS_LIST_KEY):
        if cls._next_log_lua is None:
            cls._next_log_lua = cls.get_client().register_script(_get_next_log_lua)

        if callable(cls._next_log_lua):
            return cls._next_log_lua(keys=[log_key], args=[])
        else:
            return None

    @classmethod
    def ping_redis(cls):
        """
        测试redis能否连通
        :return:
        """
        cls.get_client().ping()

    @classmethod
    def _create_redis_client(cls):
        """
        创建连接
        :return:
        """
        RedisHelper._client = redis.StrictRedis(
            host=settings.REDIS_HOST, port=settings.REDIS_PORT,
            db=settings.REDIS_DB, password=settings.REDIS_PASSWORD)

