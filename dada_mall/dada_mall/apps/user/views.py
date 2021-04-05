import json
import logging

from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView, UpdateAPIView
from rest_framework.response import Response
from django.conf import settings

from .models import User, Address
from .serializers import RegisterSerializer, LoginSerializer, AddressSerializer
from .utils import token_confirm

logger = logging.getLogger('info')


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


