from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as TJWSerializer, BadData


class User(AbstractUser):
    phone = models.CharField(max_length=11, unique=True, null=False)
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证状态')

    class Meat:
        db_name = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def generate_email_verify_url(self):
        """生成邮箱激活连接"""
        # 创建加密序列化器
        serializer = TJWSerializer(settings.SECRET_KEY, 3600 * 24)  # 指定时间
        # 调用dumps加密
        data = {
            'username': self.username,
            'email': self.email
        }
        token = serializer.dumps(data).decode()
        # 拼接激活url
        verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
        return verify_url

    @staticmethod  # 设置为静态方法
    def check_verify_email_token(token):
        """对token解密，并查询对应的user"""
        # 创建加密序列化器
        serializer = TJWSerializer(settings.SECRET_KEY, 3600 * 24)  # 指定时间
        # 调用loads解密
        try:
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            username = data.get('username')
            email = data.get('email')
            try:
                user = User.objects.get(username=username, email=email)
            except User.DoesNotExist:
                return None
            else:
                return user


