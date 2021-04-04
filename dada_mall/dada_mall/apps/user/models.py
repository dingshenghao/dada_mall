from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=11, unique=True, null=False)

    class Meat:
        db_name = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

