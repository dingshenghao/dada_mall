# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/3 下午9:04

import re

from rest_framework import serializers

from .models import User, Address
from celery_tasks.email.tasks import send_email


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'phone', 'email']
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
        password = validate_date.pop('password')
        user = User(**validate_date)
        user.set_password(password)
        user.save()
        # celery异步发送验证邮箱
        verify_url = user.generate_email_verify_url()
        send_email.delay(user.email, verify_url)
        return user


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
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


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'user_id', 'name', 'phone', 'address', 'postcode', 'tag']
        extra_kwargs = {
            'id': {'read_only': True, }
        }

    def validate_phone(self, value):
        if not re.match(r'^1[3456789]\d{9}$', value):
            raise serializers.ValidationError('请输入合法的手机号')
        return value

    def create(self, validated_data):
        address = Address(**validated_data)
        address.save()
        return address

    # def update(self, instance, validated_data):
    #     print(instance)
    #     print('---------------')
    #     instance.phone = validated_data.get('phone', instance.phone)
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.address = validated_data.get('address', instance.address)
    #     instance.tag = validated_data.get('tag', instance.tag)
    #     instance.save()
    #     return instance

