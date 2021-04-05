# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/4 下午8:59

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dada_mall.settings')

# 1.创建celery实例对象
celery_app = Celery('dada')

# 2.加载配置文件
celery_app.config_from_object('celery_tasks.config')

# 3.自动注册异步任务
celery_app.autodiscover_tasks(['celery_tasks.email'])