import json
import logging
import random

from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView
from rest_framework.response import Response
from django.conf import settings
from django_redis import get_redis_connection

from .models import User, Address
from .serializers import RegisterSerializer, LoginSerializer, AddressSerializer
from .utils import token_confirm
from celery_tasks.email.tasks import send_sms_email

logger = logging.getLogger('django')


class UserRegisterView(APIView):
    """
    用户注册
    """

    def post(self, request):
        query_dict = request.data
        # print(query_dict)
        username = query_dict['username']
        token = token_confirm.generate_validate_token(username)
        serializer = RegisterSerializer(data=query_dict)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 200, 'username': username, 'data': {'token': token}, 'carts_count': 0})


class CheckUsername(APIView):
    """
    校验用户名
    """

    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return Response({'code': 200, 'data': {'count': count}})


class CheckEmail(APIView):
    """
    校验邮箱
    """

    def get(self, request, email):
        count = User.objects.filter(email=email).count()
        return Response({'code': 200, 'data': {'count': count}})


class CheckPhone(APIView):
    """
    校验手机号
    """

    def get(self, request, phone):
        count = User.objects.filter(phone=phone).count()
        return Response({'code': 200, 'data': {'count': count}})


class UserLoginView(APIView):

    def post(self, requests):
        query_dict = requests.data
        serializer = LoginSerializer(data=query_dict)
        serializer.is_valid()
        username = query_dict['username']
        password = query_dict['password']
        token = token_confirm.generate_validate_token(username)
        if not all([username, password]):
            return Response({'error': '用户名和密码不能为空'})
        try:
            user = User.objects.get(username=username)
        except Exception as e:
            logger.info(e)
            return Response({'error': '用户名或密码错误'})
        if not check_password(password, user.password):
            return Response({'code': status.HTTP_203_NON_AUTHORITATIVE_INFORMATION, 'error': '用户名或密码错误'})
        return Response({'code': 200, 'username': username, 'carts_count': 0, 'data': {'token': token}})


class EmailVerify(APIView):

    def get(self, request):
        token = request.query_params.get('token')
        print(token)
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.check_verify_email_token(token)
        print(user)
        if not user:
            return Response({'message': '激活失败'}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active = True
        user.save()
        # 响应
        return Response({'code': 200, 'message': 'OK'})


class UserAddressView(APIView):
    """
    get: 查询地址
    post：新增地址
    """

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        addresses_model = Address.objects.filter(user_id=user.id, is_active=True)
        addresslist = []
        for address_model in addresses_model:
            address = {
                'tag': address_model.tag,
                'receiver': address_model.name,
                'address': address_model.address,
                'receiver_mobile': address_model.phone,
                'id': address_model.id,
                'is_default': address_model.is_default
            }
            addresslist.append(address)
        return Response({'code': 200, 'addresslist': addresslist})

    def post(self, request, username):
        query_dict = request.data
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '添加失败！'})
        user_id = user.id
        query_dict['user_id'] = user_id
        query_dict['phone'] = query_dict['receiver_phone']
        query_dict['name'] = query_dict['receiver']
        del query_dict['receiver']
        del query_dict['receiver_phone']
        serializer = AddressSerializer(data=query_dict)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'code': 200, 'msg': '添加成功！'})


class DeleteAddressView(APIView):
    """
    delete: 删除地址
    put： 修改地址
    """

    def delete(self, request, id, username):
        try:
            user = User.objects.get(username=username)
            address = Address.objects.get(id=id, user_id=user.id, is_Active=True)
        except Address.DoesNotExist:
            return Response({'code': 400, 'error': '删除失败！'})
        address.is_active = False
        address.save()
        return Response({'code': 200, 'msg': '删除成功！'})

    def put(self, request, username, id):
        try:
            user = User.objects.get(username=username)
            address_model = Address.objects.get(id=id, user_id=user.id, is_active=True)
        except Address.DoesNotExist:
            return Response({'code': 400, 'error': '修改失败！'})
        query_dict = json.loads(request.body.decode())
        # query_dict['user_id'] = user.id
        # query_dict['phone'] = query_dict['receiver_mobile']
        # query_dict['name'] = query_dict['receiver']
        # del query_dict['receiver']
        # del query_dict['receiver_mobile']
        # serializer = AddressSerializer(instance=address_model, data=query_dict)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        address_model.phone = query_dict['receiver_mobile']
        address_model.name = query_dict['receiver']
        address_model.address = query_dict['address']
        address_model.tag = query_dict['tag']
        address_model.save()
        return Response({'code': 200, 'msg': '修改成功！'})


class DefaultAddressView(APIView):
    """
    post: 设置默认地址
    """

    def post(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '设置失败！'})
        query_dict = request.data
        address_id = query_dict['id']
        try:
            address = Address.objects.get(user_id=user.id, id=address_id, is_active=True)
        except Address.DoesNotExist:
            return Response({'code': 400, 'error': '设置失败!'})
        user.address_id = address_id
        address.is_default = True
        default_addresses = Address.objects.filter(user_id=user.id, is_active=True, is_default=True)
        for default_address in default_addresses:
            default_address.is_default = False
            default_address.save()
        user.save()
        address.save()
        return Response({'code': 200, 'msg': '设置成功！'})


class ChangePasswordView(APIView):
    """
    post: 修改密码
    """

    def post(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '修改失败！'})
        query_dict = json.loads(request.body.decode())
        if query_dict['password1'] != query_dict['password2']:
            return Response({'code': 400, 'error': '两次密码不一致！'})
        if not check_password(query_dict['oldpassword'], user.password):
            return Response({'code': 400, 'error': '原密码错误!'})
        user.password = make_password(query_dict['password1'])
        user.save()
        return Response({'code': 200, 'msg': '修改成功！'})


class FindPaswordView(APIView):
    """
    post: 发送邮件验证码
    """

    def post(self, request):
        email = request.data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '邮箱不存在！'})
        sms_code = '%06d' % random.randint(0, 999999)
        print(sms_code)
        logger.info(sms_code)
        redis_coon = get_redis_connection('sms_code')
        send_sms_email.delay(email, sms_code)
        redis_coon.setex(email, 300, sms_code)  # 设置过期时间为5分钟
        return Response({'code': 200})


class VerifyPasswordView(APIView):
    """
    post: 认证验证码
    """

    def post(self, request):
        code = request.data['code']
        email = request.data['email']
        if not all([code, email]):
            return Response({'code': 400, 'error': '数据不能为空！'})
        redis_coon = get_redis_connection('sms_code')
        redis_sms_code = redis_coon.get(email)
        if redis_sms_code is None:
            return Response({'code': 400, 'error': '验证码已失效，请重新发送！'})
        if redis_sms_code.decode() == code:
            return Response({'code': 200})


class NewPasswordView(APIView):
    """
    post: 修改密码
    """

    def post(self, request):
        query_dict = request.data
        email = query_dict['email']
        password1 = query_dict['password1']
        password2 = query_dict['password2']
        if not all([email, password2, password1]):
            return Response({'code': 400, 'error': '数据不能为空'})
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '修改失败!'})
        if password1 != password2:
            return Response({'code': 400, 'error': '两次密码不一致！'})
        user.password = make_password(password1)
        user.save()
        return Response({'code': 200})
