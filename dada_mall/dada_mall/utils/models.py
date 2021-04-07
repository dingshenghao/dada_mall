# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/7 下午12:49

from django.db import models


class BaseModel(models.Model):
    created_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        # 设置此模型类为抽象模型类
        # 特点:1.该模型类不会有对应的mysql表2.其他模型类继承后可以获得其包含的字段
        abstract = True