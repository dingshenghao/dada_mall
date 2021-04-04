import logging

from django.contrib.auth.hashers import make_password, check_password
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response

from .models import User
from .serializers import RegisterSerializer, LoginSerializer
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
            return Response({'code': status.HTTP_203_NON_AUTHORITATIVE_INFORMATION,'error': '用户名或密码错误'})
        return Response({'code': 200,'username': username, 'carts_count': 0, 'data': {'token': token}})