from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response

from .models import User
from .serializers import RegisterSerializer
from .utils import token_confirm


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
