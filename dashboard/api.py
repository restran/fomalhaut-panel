# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals

from datetime import datetime, timedelta
import calendar
import json
import traceback
from copy import copy, deepcopy
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from cerberus import Validator
import redis
from django.db.models import Count, Sum, Q
from api_dashboard import settings
from common.utils import insert_many
from forms import *
from common.utils import http_response_json, json_dumps
from accounts.decorators import login_required
from common.utils import error_404
from tasks import parse_access_logs

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def api_get_model_data(request, model_name):
    logger.debug('run api_get_model_data')
    return_data = {'success': False, 'msg': ''}
    get_default_form = request.GET.get('get_default_form', False)
    if model_name == 'client':
        model = Client
        model_form = ClientForm
        data = model.get_all_in_json()
    elif model_name == 'endpoint':
        model = Endpoint
        model_form = EndpointForm
        data = model.get_all_in_json()
    elif model_name == 'client_endpoint':
        model = ClientEndpoint
        model_form = None
        client_id = request.GET.get('client_id')
        data = model.get_all_in_json(client_id)
    else:
        model = None
        model_form = None
        data = []

    if model is None:
        raise error_404(request)

    # 获取一个缺省值用来添加和编辑数据
    if get_default_form:
        t = model_form.get_default_form_json()
        return_data['default_form'] = t

    return_data['data'] = data
    return_data['success'] = True

    return http_response_json(return_data)


def do_create_or_update_model_data(request, model_name, is_update, post_data, form):
    return_data = {'success': False, 'msg': ''}

    if model_name == 'client_endpoint':
        client_id = post_data.get('client_id', [])
        endpoints = post_data.get('endpoints', [])
        client = Client.get_client(client_id)
        if client is None:
            return_data['msg'] = '提交的数据有误, client_id 不存在'
            return return_data

        ClientEndpoint.objects.filter(client_id=client_id).delete()
        endpoint_list = []
        for t in endpoints:
            ce = ClientEndpoint(client=client, endpoint_id=t['id'], enable=t['enable'])
            endpoint_list.append(ce)

        # bulk_create 不会返回 id
        ClientEndpoint.objects.bulk_create(endpoint_list)
        return_data['success'] = True
        return_data['data'] = ClientEndpoint.get_all_in_json(client_id)
        return return_data
    else:
        form_is_valid = form.is_valid()
        return_validation = {}
        acl_rules = post_data.get('acl_rules', [])

        if model_name == 'endpoint':
            acl_rules_validation = {'data': [], 'has_error': False, 'errors': ''}
            for t in acl_rules:
                tf = ACLRuleForm(t)
                if not tf.is_valid():
                    acl_rules_validation['has_error'] = True
                    acl_rules_validation['errors'] = '访问控制列表数据为空或不正确'
                    break

            return_validation['acl_rules'] = acl_rules_validation
            form_is_valid = form_is_valid and not acl_rules_validation['has_error']
        elif model_name == 'client_endpoint':
            pass

        if form_is_valid:
            # logger.debug(form.cleaned_data)
            logger.debug('form is valid')
            entry = form.save(commit=False)
            if model_name == 'endpoint':
                entry.save()
                acl_rules = [ACLRule(endpoint_id=entry.id,
                                     re_uri=t['re_uri'],
                                     is_permit=t['is_permit'])
                             for t in acl_rules]

                # 删除旧的
                ACLRule.objects.filter(endpoint_id=entry.id).delete()
                # 创建 ACLRule
                ACLRule.objects.bulk_create(acl_rules)
                entry.acl_rules = acl_rules
            else:
                entry.save()
            return_data['success'] = True
            return_data['data'] = entry.to_json_dict()
            logger.debug(return_data['data'])
        else:
            return_data['msg'] = '提交的数据有误'
            logger.debug('form is not valid')
            logger.debug(form.get_form_json())
            return_validation.update(form.get_form_json())
            return_data['data'] = return_validation

        return return_data


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_create_model_data(request, model_name):
    """
    创建或更新数据
    :param request:
    :param model_name:
    :return:
    """
    logger.debug('run api_create_model_data')

    post_data = json.loads(request.body)
    logger.debug(post_data)
    if model_name == 'client':
        form = ClientForm(post_data['data'])
    elif model_name == 'endpoint':
        form = EndpointForm(post_data['data'])
    elif model_name == 'client_endpoint':
        form = None
    else:
        form = None

    return_data = do_create_or_update_model_data(
        request, model_name, False, post_data, form)
    return http_response_json(return_data)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_update_model_data(request, model_name, entry_id):
    """
    创建或更新数据
    :param request:
    :param model_name:
    :param entry_id:
    :return:
    """
    logger.debug('run api_update_model_data')
    return_data = {'success': False, 'msg': ''}

    if model_name == 'client':
        model = Client
        model_form = ClientForm
    elif model_name == 'endpoint':
        model = Endpoint
        model_form = EndpointForm
    elif model_name == 'client_endpoint':
        model = None
        model_form = None
    else:
        model = None
        model_form = None

    post_data = json.loads(request.body)
    logger.debug(post_data)

    if model_name != 'client_endpoint':
        try:
            entry = model.objects.get(id=entry_id)
        except models.Model.DoesNotExist:
            return_data['msg'] = '数据不存在'
            return http_response_json(return_data)

        if model_name == 'client':
            form = model_form(post_data['data'], instance=entry)
        elif model_name == 'endpoint':
            form = model_form(post_data['data'], instance=entry)
        else:
            form = None
    else:
        form = None

    return_data = do_create_or_update_model_data(
        request, model_name, True, post_data, form)
    return http_response_json(return_data)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_delete_model_data(request, model_name, entry_id=None):
    """
    删除数据
    :param request:
    :param model_name:
    :param entry_id:
    :return:
    """
    logger.debug('run api_delete_model_data')
    return_data = {'success': False, 'msg': ''}
    if model_name == 'client':
        model = Client
    elif model_name == 'endpoint':
        model = Endpoint
    elif model_name == 'client_endpoint':
        model = ClientEndpoint
    else:
        model = None

    if model and entry_id is not None:
        try:
            entry = model.objects.get(id=entry_id)
            entry.delete()
            return_data['success'] = True
        except models.Model.DoesNotExist:
            return_data['msg'] = u'数据不存在'

    return http_response_json(return_data)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_update_enable_state_model_data(request, model_name, entry_id=None):
    """
    点击启用按钮，更新启用状态
    :param request:
    :param model_name:
    :param entry_id:
    :return:
    """
    logger.debug('run api_update_enable_state_model_data')
    return_data = {'success': False, 'msg': ''}
    if model_name == 'client':
        model = Client
    elif model_name == 'endpoint':
        model = Endpoint
    elif model_name == 'client_endpoint':
        model = ClientEndpoint
    else:
        model = None

    post_data = json.loads(request.body)
    if model and entry_id:
        try:
            model.objects.filter(id=entry_id).update(enable=post_data['enable'])
            return_data['success'] = True
        except Exception as e:
            logger.error(e.message)
            return_data['msg'] = u'更新启用状态失败'

    return http_response_json(return_data)


def do_import_config(upload_file):
    """
    从json文件导入配置
    :param upload_file:
    :return:
    """
    file_contents = upload_file.read()
    try:
        json_data = json.loads(file_contents)
    except Exception as e:
        logger.error(e.message)
        return False, u'上传的文件不是JSON或者格式有误', []

    json_data_schema = {
        'clients': {
            'type': 'list',
            'required': True,
            'schema': {
                'type': 'dict',
                'schema': {
                    'id': {
                        'type': 'integer',
                        'required': True,
                    },
                    'name': {
                        'type': 'string',
                        'required': True,
                    },
                    'access_key': {
                        'type': 'string',
                        'required': True,
                    },
                    'secret_key': {
                        'type': 'string',
                        'required': True,
                    },
                    'enable': {
                        'type': 'boolean',
                        'required': True,
                    },
                    'memo': {
                        'type': 'string',
                        'required': True,
                    }
                }
            }
        },
        'client_endpoints': {
            'type': 'list',
            'required': True,
            'schema': {
                'type': 'dict',
                'schema': {
                    'id': {
                        'type': 'integer',
                        'required': True,
                    },
                    'client_id': {
                        'type': 'integer',
                        'required': True,
                    },
                    'endpoint_id': {
                        'type': 'integer',
                        'required': True,
                    },
                    'enable': {
                        'type': 'boolean',
                        'required': True,
                    }
                }
            }
        },
        'endpoints': {
            'type': 'list',
            'required': True,
            'schema': {
                'type': 'dict',
                'schema': {
                    'id': {
                        'type': 'integer',
                        'required': True,
                    },
                    'unique_name': {
                        'type': 'string',
                        'required': True,
                    },
                    'name': {
                        'type': 'string',
                        'required': True,
                    },
                    'version': {
                        'type': 'string',
                        'required': True,
                    },
                    'url': {
                        'type': 'string',
                        'required': True,
                    },
                    'memo': {
                        'type': 'string',
                        'required': True,
                    },
                    'async_http_connect_timeout': {
                        'type': 'integer',
                        'required': True,
                    },
                    'async_http_request_timeout': {
                        'type': 'integer',
                        'required': True,
                    },
                    'enable_acl': {
                        'type': 'boolean',
                        'required': True,
                    },
                    'acl_rules': {
                        'type': 'list',
                        'required': True,
                        'schema': {
                            'type': 'dict',
                            'schema': {
                                'is_permit': {
                                    'type': 'boolean',
                                    'required': True,
                                },
                                're_uri': {
                                    'type': 'string',
                                    'required': True,
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    validator = Validator(json_data_schema)
    validator.allow_unknown = True
    if not validator.validate(json_data):
        errors = []
        for (k, v) in validator.errors.items():
            errors.append('%s: %s' % (k, v))
        return False, u'上传的 JSON 配置文件格式有误，请先导出 JSON 配置文件再修改', errors
    else:
        success, msg, errors = False, '', []
        try:
            # 出现异常的时候，会自动回滚
            with transaction.atomic():
                # 清除旧的数据，不包含 Client 和 Endpoint
                ClientEndpoint.objects.all().delete()
                ACLRule.objects.all().delete()
                old_client_list = Client.objects.all()
                old_client_dict = {}
                for t in old_client_list:
                    old_client_dict[t.access_key] = t

                old_endpoint_list = Endpoint.objects.all()
                old_endpoint_dict = {}
                for t in old_endpoint_list:
                    old_endpoint_dict[t.unique_name] = t

                new_client_dict = {}
                for t in json_data['clients']:
                    # del t['id']
                    old_client = old_client_dict.get(t['access_key'])
                    # 如果已存在相同的，则更新
                    if old_client is not None:
                        form = ClientForm(t, instance=old_client)
                        del old_client_dict[t['access_key']]
                    else:
                        form = ClientForm(t)
                    if not form.is_valid():
                        errors = []
                        form_errors = form.get_form_json()
                        for (k, v) in form_errors.items():
                            if v['has_error']:
                                errors.append('%s: %s' % (k, v['errors']))
                        msg, errors = u'上传的 JSON 配置文件格式有误，请先导出 JSON 配置文件再修改', errors
                        raise Exception('error')

                    client = form.save()
                    new_client_dict[t['id']] = client

                new_endpoint_dict = {}
                for t in json_data['endpoints']:
                    # del t['id']
                    old_endpoint = old_endpoint_dict.get(t['unique_name'])
                    # 如果已存在相同的，则更新
                    if old_endpoint is not None:
                        form = EndpointForm(t, instance=old_endpoint)
                        del old_endpoint_dict[t['unique_name']]
                    else:
                        form = EndpointForm(t)
                    if not form.is_valid():
                        errors = []
                        form_errors = form.get_form_json()
                        for (k, v) in form_errors.items():
                            if v['has_error']:
                                errors.append('%s: %s' % (k, v['errors']))
                        msg, errors = u'上传的 JSON 配置文件格式有误，请先导出 JSON 配置文件再修改', errors
                        raise Exception('error')

                    endpoint = form.save(commit=False)
                    endpoint.save()
                    new_endpoint_dict[t['id']] = endpoint

                    acl_rules = t['acl_rules']
                    for y in acl_rules:
                        # del t['id']
                        tf = ACLRuleForm(y)
                        if not tf.is_valid():
                            msg, errors = u'上传的 JSON 配置文件格式有误，请先导出 JSON 配置文件再修改', \
                                          [u'访问控制列表数据为空或不正确']
                            raise Exception('error')

                    acl_rules = [ACLRule(endpoint_id=endpoint.id,
                                         re_uri=t['re_uri'], is_permit=t['is_permit'])
                                 for t in acl_rules]
                    # 创建 ACLRule
                    ACLRule.objects.bulk_create(acl_rules)

                # 根据新的 id 匹配正确的 client_endpoint
                client_endpoint_list = []
                for t in json_data['client_endpoints']:
                    client = new_client_dict.get(t['client_id'])
                    endpoint = new_endpoint_dict.get(t['endpoint_id'])
                    enable = t['enable']
                    ce = ClientEndpoint(client=client, endpoint=endpoint, enable=enable)
                    client_endpoint_list.append(ce)
                ClientEndpoint.objects.bulk_create(client_endpoint_list)

                # 删除导入的配置中，不存在的 Client
                Client.objects.filter(id__in=[t.id for t in old_client_dict.values()]).delete()
                # 删除导入的配置中，不存在的 Endpoint
                Endpoint.objects.filter(id__in=[t.id for t in old_endpoint_dict.values()]).delete()

                success, msg = True, u'导入配置成功'
        except Exception as e:
            logger.error(e.message)

        return success, msg, errors


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_import_config(request):
    """
    上传文件，导入配置
    """
    if request.FILES:
        success, msg, errors = False, '', []
        for _file in request.FILES:
            # 关闭了分块上传，上传上来的就是完整的
            # 只允许选择一份文件，处理完就break
            success, msg, errors = do_import_config(request.FILES[_file])
            break

        return http_response_json({'success': success, 'msg': msg, 'errors': errors})
    else:
        raise error_404(request)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_transfer_to_redis(request):
    """
    将配置数据同步到Redis中
    """
    success, msg = False, ''
    try:
        config_data = get_config_redis_json()
        logger.debug(config_data)
        r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                              db=settings.REDIS_DB, password=settings.REDIS_PASSWORD)

        # 默认transaction=True
        pipe = r.pipeline(transaction=True)
        # 按模式匹配批量删除
        pattern_delete_lua = """
        local keys = redis.call('keys', ARGV[1])
        for i = 1, table.getn(keys) do
            redis.call('del', keys[i])
        end
        """
        pattern_delete = r.register_script(pattern_delete_lua)
        pattern_delete(keys=[''], args=['%s:*' % settings.PROXY_CONFIG_REDIS_PREFIX], client=pipe)

        for t in config_data:
            logger.debug(t)

            client = {}
            for k, v in t.iteritems():
                if k != 'endpoints':
                    client[k] = v
            pipe.set('%s:%s' % (settings.PROXY_CONFIG_REDIS_PREFIX, t['access_key']), json_dumps(client))

            for s in t['endpoints']:
                pipe.set('%s:%s:%s:%s' % (settings.PROXY_CONFIG_REDIS_PREFIX, t['access_key'], s['name'], s['version']),
                         json_dumps(s))
        # pipe.delete('config:*')

        # the EXECUTE call sends all buffered commands to the server, returning
        # a list of responses, one for each command.
        pipe.execute()
        success = True
    except Exception as e:
        msg = u'同步配置数据到 Redis 出现异常'
        logger.error(e.message)
        logger.error(traceback.format_exc())

    return http_response_json({'success': success, 'msg': msg})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_get_total_by_day_access(request):
    """
    获取24小时访问统计
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    request_type = post_data.get('request_type', 'all')
    logger.debug(post_data)
    date = datetime.strptime(post_data['date'], '%Y-%m-%d').date()
    if date == datetime.today().date():
        max_hour = datetime.now().hour + 1
    else:
        max_hour = 24

    agent_id_list = post_data['agent_id_list']

    count_data = []
    for aid in agent_id_list:
        if aid <= -100:
            result_code = abs(aid) - 100
            count_list = AccessLog.objects.filter(
                result_code=result_code, date=date).values('hour').annotate(count=Count('id'))
        elif aid != -1:
            if request_type == 'all':
                count_list = AccessLog.objects.filter(
                    agent_id=aid, date=date).values('hour').annotate(count=Count('id'))
            else:
                count_list = AccessLog.objects.filter(
                    agent_id=aid, date=date, header_token=True).values('hour').annotate(count=Count('id'))
        else:
            if request_type == 'all':
                # 所有
                count_list = AccessLog.objects.filter(
                    date=date).values('hour').annotate(count=Count('id'))
            else:
                count_list = AccessLog.objects.filter(
                    date=date, header_token=True).values('hour').annotate(count=Count('id'))

        count_dict = {}
        for t in count_list:
            t['hour'] = int(t['hour'])
            count_dict[t['hour']] = t

        logger.debug(count_list)

        new_count_list = []
        for t in range(max_hour):
            if t not in count_dict:
                new_count_list.append(0)
            else:
                new_count_list.append(count_dict[t]['count'])

        count_data.append(new_count_list)
        logger.debug(new_count_list)

    success = True
    return http_response_json({'success': success, 'msg': msg, 'data': count_data,
                               'x-data': range(0, 24)})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_get_total_by_month_access(request):
    """
    获取月访问统计
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    request_type = post_data.get('request_type', 'all')
    year = int(post_data['year'])
    month = int(post_data['month'])
    _, month_max_day = calendar.monthrange(year, month)
    today = datetime.today().date()
    if month == today.month and year == today.year:
        max_day = today.day + 1
    else:
        max_day = month_max_day + 1

    min_date = datetime(year=year, month=month, day=1)
    max_date = datetime(year=year, month=month, day=month_max_day)
    agent_id_list = post_data['agent_id_list']
    count_data = []
    for aid in agent_id_list:
        if aid <= -100:
            result_code = abs(aid) - 100
            count_list = AccessLog.objects.filter(
                result_code=result_code, date__gte=min_date, date__lte=max_date). \
                values('date').annotate(m_count=Count('id'))
        elif aid != -1:
            if request_type == 'all':
                count_list = AccessLog.objects.filter(agent_id=aid, date__gte=min_date, date__lte=max_date). \
                    values('date').annotate(m_count=Count('id'))
            else:
                count_list = AccessLog.objects.filter(agent_id=aid, header_token=True, date__gte=min_date,
                                                      date__lte=max_date). \
                    values('date').annotate(m_count=Count('id'))
        else:
            if request_type == 'all':
                # 所有
                count_list = AccessDayCounter.objects.filter(date__gte=min_date, date__lte=max_date). \
                    values('date').annotate(m_count=Sum('count'))
            else:
                count_list = AccessDayCounter.objects.filter(page_view=True, date__gte=min_date, date__lte=max_date). \
                    values('date').annotate(m_count=Sum('count'))

        count_dict = {}
        for t in count_list:
            day = t['date'].day
            count_dict[day] = t

        logger.debug(count_list)

        new_count_list = []
        for t in range(1, max_day):
            if t not in count_dict:
                new_count_list.append(0)
            else:
                new_count_list.append(count_dict[t]['m_count'])

        count_data.append(new_count_list)
        logger.debug(new_count_list)

    success = True
    return http_response_json({'success': success, 'msg': msg, 'data': count_data,
                               'x-data': range(1, month_max_day + 1)})


@login_required
@csrf_protect
@require_http_methods(["GET"])
def api_get_total_count(request):
    """
    获取累计访问数量
    """
    success, msg, data = False, '', []
    # 查看类型，是查看所有请求，还是只查看页面访问
    request_type = request.GET.get('request_type', 'all')
    logger.debug(request_type)
    if request_type == 'all':
        total_count = AccessDayCounter.objects.aggregate(total_count=Sum('count'))
        today_count = AccessDayCounter.objects.filter(
            date=datetime.today().date()).aggregate(
            today_count=Sum('count'))

        yesterday_count = AccessDayCounter.objects.filter(
            date=datetime.today().date() - timedelta(days=1)).aggregate(
            yesterday_count=Sum('count'))
    else:
        total_count = AccessDayCounter.objects.filter(
            page_view=True).aggregate(total_count=Sum('count'))
        logger.debug(total_count)
        today_count = AccessDayCounter.objects.filter(
            date=datetime.today().date(),
            page_view=True).aggregate(today_count=Sum('count'))

        yesterday_count = AccessDayCounter.objects.filter(
            date=datetime.today().date() - timedelta(days=1),
            page_view=True).aggregate(yesterday_count=Sum('count'))

    data = {}
    data.update(total_count)
    data.update(today_count)
    data.update(yesterday_count)

    for k, v in data.iteritems():
        if v is None:
            data[k] = 0

    logger.debug(data)

    success = True
    return http_response_json({'success': success, 'msg': msg, 'data': data})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_get_ip_count(request):
    """
    获取IP访问统计数量
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    # 查看类型，是查看所有请求，还是只查看页面访问
    request_type = post_data.get('request_type', 'all')
    date = post_data.get('date')
    if date:
        date = datetime.strptime(post_data['date'], '%Y-%m-%d').date()
        min_date = date
        max_date = date
    else:
        year = int(post_data['year'])
        month = int(post_data['month'])
        _, month_max_day = calendar.monthrange(year, month)

        min_date = datetime(year=year, month=month, day=1)
        max_date = datetime(year=year, month=month, day=month_max_day)

    agent_id_list = [t for t in post_data['agent_id_list'] if t >= -1]
    result_code_list = [abs(t) - 100 for t in post_data['agent_id_list'] if t <= -100]

    # 是否请求所有的应用
    all_agents = False
    for t in post_data['agent_id_list']:
        if t == -1:
            all_agents = True
            break

    if all_agents:
        if request_type == 'all':
            ip_count_list = AccessLog.objects.filter(
                date__gte=min_date, date__lte=max_date).values(
                'remote_ip').annotate(m_count=Count('id')).order_by('-m_count')[:10]
        else:
            # 使用 header token 来判断是否属于页面访问
            ip_count_list = AccessLog.objects.filter(
                date__gte=min_date, date__lte=max_date,
                header_token=True).values(
                'remote_ip').annotate(m_count=Count('id')).order_by('-m_count')[:10]
    else:
        if request_type == 'all':
            ip_count_list = AccessLog.objects.filter(
                (Q(result_code__in=result_code_list) |
                 Q(agent_id__in=agent_id_list)) & Q(
                    date__gte=min_date, date__lte=max_date)).values(
                'remote_ip').annotate(m_count=Count('id')).order_by('-m_count')[:10]
        else:
            ip_count_list = AccessLog.objects.filter(
                (Q(result_code__in=result_code_list) |
                 Q(agent_id__in=agent_id_list)) & Q(
                    header_token=True,
                    date__gte=min_date, date__lte=max_date)).values(
                'remote_ip').annotate(m_count=Count('id')).order_by('-m_count')[:10]

    # 因为返回的是 QuerySet，不这样处理会出现 not JSON serializable
    ip_count_list = list(ip_count_list)
    logger.debug(ip_count_list)
    success = True
    return http_response_json({'success': success, 'msg': msg, 'data': ip_count_list})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_get_abnormal_ip_count(request):
    """
    获取异常访问IP统计数量
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    date = post_data.get('date')
    if date:
        date = datetime.strptime(post_data['date'], '%Y-%m-%d').date()
        min_date = date
        max_date = date
    else:
        year = int(post_data['year'])
        month = int(post_data['month'])
        _, month_max_day = calendar.monthrange(year, month)

        min_date = datetime(year=year, month=month, day=1)
        max_date = datetime(year=year, month=month, day=month_max_day)

    ip_count_list = AccessLog.objects.filter(
        result_code=ACCESS_RESULT_FORBIDDEN,
        date__gte=min_date, date__lte=max_date).values(
        'remote_ip').annotate(m_count=Count('id')).order_by('-m_count')[:5]

    # 因为返回的是 QuerySet，不这样处理会出现 not JSON serializable
    ip_count_list = list(ip_count_list)
    logger.debug(ip_count_list)
    success = True
    return http_response_json({'success': success, 'msg': msg, 'data': ip_count_list})


@login_required
@csrf_protect
@require_http_methods(["GET"])
def api_get_access_agent_options(request):
    """
    获取AccessAgent，select 选项
    """
    success, msg, data = False, '', []
    data = Client.objects.all().values('id', 'name')
    data = [t for t in data]
    success = True
    logger.debug(data)
    return http_response_json({'success': success, 'msg': msg, 'data': data})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_get_access_log(request):
    """
    获取访问日志
    :param request:
    :return:
    """
    success, msg, data = False, '', []
    post_data = json.loads(request.body)
    date = datetime.strptime(post_data['date'], '%Y-%m-%d').date()
    page_id = post_data.get('page_id', 1)
    agent_id_list = post_data['agent_id_list']
    for t in agent_id_list:
        if t == -1:
            agent_id_list = None
            break

    result_code_list = post_data['result_code_list']
    for t in result_code_list:
        if t == '-1':
            result_code_list = None
            break

    page_size = settings.DEFAULT_ACCESS_LOG_PAGE_SIZE
    data, total_num, has_previous_page, has_next_page, offset \
        = AccessLog.get_page_in_json(date, agent_id_list, result_code_list, page_id)
    # 总页数
    total_page = total_num / page_size

    if total_num == page_size:
        # 0 表示只有1页
        total_page = 0

    logger.debug("total_num: " + str(total_num))
    if page_id > total_page + 1:
        return error_404(request)

    # display表示是否需要显示分页
    page_info = {'display': True, 'previous_page': page_id - 1, 'next_page': page_id + 1,
                 'has_previous_page': has_previous_page, 'has_next_page': has_next_page,
                 'offset': offset, 'total_num': total_num, 'total_page': total_page + 1}

    if len(data) > 0:
        if total_page <= 0:  # 0 表示只有1页
            # 不显示分页信息
            page_info['display'] = False
        elif total_page < 7:
            page_info['page_list'] = range(1, total_page + 2)
            # 这里的active采用与forloop.counter比较
            # forloop.counter是从1开始的
            page_info['active'] = page_id
        else:
            page_info['page_list'] = [1, 2, '...', '...', '...', total_page, total_page + 1]
            if page_id < 3:
                page_info['active'] = page_id
            elif page_id == 3:
                page_info['active'] = 3
                page_info['page_list'][2] = page_id
            elif page_id == total_page - 1:
                page_info['active'] = 5
                page_info['page_list'][4] = page_id
            elif page_id > total_page - 1:
                page_info['active'] = 7 - (total_page + 1 - page_id)
            else:
                page_info['active'] = 4
                page_info['page_list'][3] = page_id
    else:
        page_info['display'] = False

    return http_response_json({'success': True, 'msg': msg,
                               'data': data, 'page_info': page_info})


@login_required
@csrf_protect
@require_http_methods(["POST"])
def api_refresh_access_log(request):
    """
    立即从redis中更新访问日志
    :param request:
    :return:
    """
    success, msg, data = False, '', []
    parse_access_logs()
    return http_response_json({'success': True, 'msg': msg})
