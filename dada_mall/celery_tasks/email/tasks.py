# -*- encode: utf-8 -*-
# @Author: dsh
# Time: 2021/4/4 下午9:01
from django.conf import settings

from django.core.mail import send_mail

from celery_tasks.main import celery_app


@celery_app.task(name='send_email')
def send_email(to_email, verify_url):
    """
    发送验证邮箱
    :param to_email: 收件人邮箱
    :param verify_url: 验证链接
    :return:
    """
    subject = "达达商城邮箱验证"
    html_message = '<p>尊敬的⽤户您好！</p>' \
                   '<p>感谢您使⽤达达商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    # send_mail(subject：标题，message：普通文本内容，发件人，收件人（可以是列表），html_message：超文本邮箱内容)
    send_mail(subject, '', settings.EMAIL_FROM, [to_email], html_message=html_message)
