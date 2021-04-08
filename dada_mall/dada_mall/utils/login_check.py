# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/8 下午8:11
import logging
from django.http import JsonResponse

from user.models import User
from user.utils import token_confirm


logger = logging.getLogger('django')


def login_check(func):
    def wrapper(self, request, *args, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            result = {"code": 403, "error": "Please login"}
            return JsonResponse(result)
        try:
            username = token_confirm.confirm_validate_token(token)
        except Exception as e:
            logger.info(e)
            result = {"code": 403, "error": "Please login"}
            return JsonResponse(result)
        user = User.objects.get(username=username)
        request.user = user
        return func(self, request, *args, **kwargs)
    return wrapper
