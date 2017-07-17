# -*- coding: utf-8 -*-
# Created by restran on 2016/7/27
from __future__ import unicode_literals, absolute_import
from fabric.api import *
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 登录用户和主机名：
env.user = 'root'
# env.password = 'password'
# 如果有多个主机，fabric会自动依次部署
env.hosts = ['192.168.14.101']

TAR_FILE_NAME = 'fomalhaut_dashboard_deploy.tar.gz'


def pack():
    """
    定义一个pack任务, 打一个tar包
    :return:
    """
    local('rm -rf dist')
    local('fis3 release -d dist')

    tar_files = ['*.py', 'static/*', 'templates/*', 'common/*',
                 'fomalhaut/*', 'dashboard/*', 'accounts/*', 'requirements.txt']
    exclude_files = ['fabfile.py', 'deploy/*', '*.tar.gz', '.DS_Store', '*/.DS_Store', '__pycache__/*', '*.log']
    exclude_files = ['--exclude=\'%s\'' % t for t in exclude_files]
    local('rm -f %s' % TAR_FILE_NAME)
    with lcd('dist'):
        local('tar -czvf %s %s %s' %
              (TAR_FILE_NAME, ' '.join(exclude_files), ' '.join(tar_files)))

    print('在当前目录创建一个打包文件: %s' % TAR_FILE_NAME)


def backup():
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = '/home/backup/fomalhaut_dashboard_%s.tar.gz' % now
    # 如果不存在, 则创建文件夹
    run('mkdir -p /home/backup')
    exclude_files = ['*.log', '*.pyc']
    exclude_files = ['--exclude=\'%s\'' % t for t in exclude_files]
    run('tar -czvf %s %s /home/python/fomalhaut_dashboard' % (backup_file, ' '.join(exclude_files)))

    print('创建备份文件: %s' % backup_file)


def deploy():
    """
    定义一个部署任务
    :return:
    """
    # 先进行打包
    pack()
    # 备份服务器上的版本
    backup()

    # 远程服务器的临时文件
    remote_tmp_tar = '/tmp/%s' % TAR_FILE_NAME
    run('rm -f %s' % remote_tmp_tar)
    # 上传tar文件至远程服务器
    put('dist/%s' % TAR_FILE_NAME, remote_tmp_tar)
    # 解压
    remote_dist_dir = '/home/python/fomalhaut_dashboard'

    # 如果不存在, 则创建文件夹
    run('mkdir -p %s' % remote_dist_dir)

    name = 'fomalhaut_dashboard'

    with cd(remote_dist_dir):
        print('解压文件到到目录: %s' % remote_dist_dir)
        run('tar -xzvf %s' % remote_tmp_tar)
        print('安装 requirements.txt 中的依赖包')
        run('pip install -r requirements.txt')
        remote_settings_file = '%s/fomalhaut/settings.py' % remote_dist_dir
        settings_file = 'deploy/settings.py'
        print('上传 settings.py 文件 %s' % settings_file)
        put(settings_file, remote_settings_file)

        # 创建日志文件夹, 因为当前启动 django 进程用的是 nobody, 会没有权限
        remote_logs_path = '%s/logs' % remote_dist_dir
        # 如果不存在, 则创建文件夹
        run('mkdir -p %s' % remote_logs_path)

        nginx_file = 'deploy/%s.conf' % name
        remote_nginx_file = '/etc/nginx/conf.d/%s.conf' % name
        print('上传 nginx 配置文件 %s' % nginx_file)
        put(nginx_file, remote_nginx_file)
        print('设置文件夹权限')
        run('chown -R oxygen /home/python/%s' % name)

        supervisor_file = 'deploy/%s.ini' % name
        remote_supervisor_file = '/etc/supervisord.d/%s.ini' % name
        print('上传 supervisor 配置文件 %s' % supervisor_file)
        put(supervisor_file, remote_supervisor_file)

    run('supervisorctl reload')
    run('nginx -s reload')
    run('nginx -t')
    run('supervisorctl restart fomalhaut_dashboard:')
    run('supervisorctl restart fomalhaut_celery_beat:')
    run('supervisorctl restart fomalhaut_celery_worker:')
    # run('service nginx restart')
    # 删除本地的打包文件
    local('rm -f %s' % TAR_FILE_NAME)
    local('rm -rf dist')
    # run('supervisorctl restart ')



