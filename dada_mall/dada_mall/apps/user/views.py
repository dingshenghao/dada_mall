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

