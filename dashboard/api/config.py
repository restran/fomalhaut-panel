# !/usr/bin/env python
# -*- coding: utf-8 -*-
# created by restran on 2016/1/2

from __future__ import unicode_literals, absolute_import

import traceback

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.db import transaction

from cerberus import Validator
import redis

from api_dashboard import settings
from ..forms import *
from common.utils import http_response_json, json_dumps, json_loads
from accounts.decorators import login_required
from common.utils import error_404

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def get_model_data(request, model_name):
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
def create_model_data(request, model_name):
    """
    创建或更新数据
    :param request:
    :param model_name:
    :return:
    """
    logger.debug('run api_create_model_data')

    post_data = json_loads(request.body)
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
def update_model_data(request, model_name, entry_id):
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

    post_data = json_loads(request.body)
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
def delete_model_data(request, model_name, entry_id=None):
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
def update_enable_state_model_data(request, model_name, entry_id=None):
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

    post_data = json_loads(request.body)
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
        json_data = json_loads(file_contents)
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

    validator = Validator(json_data_schema, allow_unknown=True)
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
def import_config(request):
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
def transfer_to_redis(request):
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
        pattern_delete(keys=[''], args=['%s:*' % settings.CLIENT_CONFIG_REDIS_PREFIX], client=pipe)

        for t in config_data:
            logger.debug(t)
            #
            # client = {}
            # for k, v in t.iteritems():
            #     if k != 'endpoints':
            #         client[k] = v
            pipe.set('%s:%s' % (settings.CLIENT_CONFIG_REDIS_PREFIX, t['access_key']), json_dumps(t))

            # for s in t['endpoints']:
            #     pipe.set('%s:%s:%s:%s' % (settings.PROXY_CONFIG_REDIS_PREFIX, t['access_key'], s['name'], s['version']),
            #              json_dumps(s))
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
