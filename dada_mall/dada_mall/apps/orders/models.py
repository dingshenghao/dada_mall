from django.db import models

from dada_mall.utils.models import BaseModel

STATUS_CHOICES = (
    (1, "待付款"),
    (2, "待发货"),
    (3, "待收货"),
    (4, "订单完成")
)


class OrderInfo(BaseModel):
    order_id = models.CharField(max_length=64, verbose_name="订单id", primary_key=True)
    user_id = models.IntegerField(verbose_name='用户id')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="商品金额")
    total_count = models.IntegerField(verbose_name="商品总数")
    pay_method = models.SmallIntegerField(default=1, verbose_name="支付方式")
    freight = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="运费")
    status = models.SmallIntegerField(verbose_name="订单状态", choices=STATUS_CHOICES)
    # 订单地址(冗余数据)
    receiver = models.CharField(max_length=10, verbose_name="收件人")
    address = models.CharField(max_length=100, verbose_name="收货地址")
    receiver_mobile = models.CharField(max_length=11, verbose_name="手机号")
    tag = models.CharField(max_length=10, verbose_name="标签")

    class Meta:
        db_table = "order_order_info"


class OrderGoods(BaseModel):
    # 订单商品表
    # 做外键关联订单信息表
    order_info = models.ForeignKey(OrderInfo, on_delete=models.CASCADE)
    sku_id = models.IntegerField(verbose_name='商品sku_id')
    count = models.IntegerField(default=1, verbose_name="数量")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="单价")

    class Meta:
        db_table = "order_order_goods"
