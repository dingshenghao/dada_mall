# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/3 下午9:04

import re

from rest_framework import serializers

from .models import User
from .utils import token_confirm


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'phone']
        extra_kwargs = {
            'username': {
                'min_length': 6,
                'max_length': 11,
                'error_messages': {
                    'min_length': '用户名长度在6到11位之间',
                    'max_length': '用户名长度在6到11位之间'
                }
            },
            'password': {
                'min_length': 6,
                'max_length': 12,
                'error_messages': {
                    'min_length': '密码长度在6到12位之间',
                    'max_length': '密码长度在6到12位之间'
                }
            }
        }

    def validate_phone(self, value):
        if not re.match(r'^1[3456789]\d{9}$', value):
            raise serializers.ValidationError('请输入合法的手机号')
        return value

    def validate_email(self, value):
        if not re.match(r'^[a-zA-Z0-9_.-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z0-9]{2,6}$', value):
            raise serializers.ValidationError('请输入合法的邮箱地址')
        return value

    def create(self, validate_date):
        # print(validate_date)
        password = validate_date.pop('password')
        user = User(**validate_date)
        user.set_password(password)
        user.save()
        return user

