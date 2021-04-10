from datetime import datetime
import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from django_redis import get_redis_connection
from django.conf import settings
from django.db import transaction

from goods.models import SPUSaleAttr, SKU, SPU
from orders.models import OrderInfo, STATUS_CHOICES, OrderGoods
from user.models import User, Address

logger = logging.getLogger('django')


class OrderView(APIView):

    def get(self, request, username):
        settlement_type = request.query_params['settlement_type']
        redis_coon = get_redis_connection('default')
        if not settlement_type:
            return Response({"code": 10500, "error": "please give me type"})
        settlement_type = int(settlement_type)
        try:
            user = User.objects.get(username=username)
        except User.DoexNotExist:
            return Response({'code': 400, 'error': '数据出现错误'})
        addresses_model = Address.objects.filter(user_id=user.id)
        default_address = []
        no_default_address = []
        for address_model in addresses_model:
            address = {
                'id': address_model.id,
                'address': address_model.address,
                'name': address_model.name,
                'mobile': address_model.phone,
                'title': address_model.tag
            }
            if address_model.is_default:
                default_address.append(address)
            else:
                no_default_address.append(address)
        if settlement_type == 0:
            redis_bytes_skus = redis_coon.hgetall('cart_%d' % user.id)
            carts = []
            for redis_bytes_sku_id in redis_bytes_skus:
                sku_id = int(redis_bytes_sku_id)
                count = int(redis_bytes_skus[redis_bytes_sku_id])
                sku = SKU.objects.get(id=sku_id)
                spu_id = sku.spu_id
                sku_sale_attr_name = [i.name for i in SPUSaleAttr.objects.filter(spu_id=spu_id)]
                sku_sale_attr_val = [i.name for i in sku.sale_attr_value.all()]
                cart = {
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': str(sku.default_image_url),
                    'sku_sale_attr_name': sku_sale_attr_name,
                    'sku_sale_attr_val': sku_sale_attr_val,
                    'price': str(sku.price),
                    'count': count,
                }
                if redis_coon.sismember('is_select_%s' % user.username, cart['id']):
                    carts.append(cart)
        else:
            sku_id = request.query_params['sku_id']
            count = request.query_params['buy_num']
            try:
                sku = SKU.objects.get(id=sku_id)
            except SKU.DoesNotExist:
                return Response({'code': 400, 'error': '数据出现错误'})
            carts = []
            spu_id = sku.spu_id
            sku_sale_attr_name = [i.name for i in SPUSaleAttr.objects.filter(spu_id=spu_id)]
            sku_sale_attr_val = [i.name for i in sku.sale_attr_value.all()]
            cart = {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': str(sku.default_image_url),
                'sku_sale_attr_name': sku_sale_attr_name,
                'sku_sale_attr_val': sku_sale_attr_val,
                'price': str(sku.price),
                'count': count,
            }
            carts.append(cart)
        return Response(
            {'code': 200, 'data': {'addresses': default_address + no_default_address, 'sku_list': carts},
             'base_url': settings.PIC_URL})


class OrderCommitView(APIView):

    def post(self, request, username):
        query_dict = request.data
        address_id = query_dict['address_id']
        settlement_type = query_dict['settlement_type']
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return Response({'code': 400, 'error': '数据出现错误'})
        user = User.objects.get(username=username)
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + ('%09d' % user.id)
        with transaction.atomic():  # 手动开启数据库事物
            try:
                save_id = transaction.savepoint()  # 创建事务保存点
                total_amount = 0
                total_count = 0
                order_info = OrderInfo.objects.create(
                    order_id=order_id,
                    user_id=user.id,
                    address=address.address,
                    receiver=address.name,
                    receiver_mobile=address.phone,
                    tag=address.tag,
                    total_amount=total_amount,
                    total_count=total_count,
                    freight=1,
                    pay_method=1,
                    status=1
                )
                redis_coon = get_redis_connection('default')
                redis_bytes_skus = redis_coon.hgetall('cart_%d' % user.id)
                selected_ids = redis_coon.smembers('is_select_%s' % user.username)
                carts = {}
                for sku_id_bytes in selected_ids:
                    carts[int(sku_id_bytes)] = int(redis_bytes_skus[sku_id_bytes])
                skus_id = carts.keys()
                for sku_id in skus_id:
                    while True:
                        sku = SKU.objects.get(id=sku_id)
                        buy_count = carts[sku_id]
                        # 修改sku销量与库存
                        origin_stock = sku.stock  # sku原库存
                        origin_sales = sku.sales  # sku原销量
                        if buy_count > origin_stock:
                            transaction.savepoint_rollback(save_id)  # 下单失败，回滚到事物保存点
                            return Response({'code': 400, 'errmsg': '库存不足'})
                        # 购买成功，修改sku销量与库存
                        # sku.stock = origin_stock - buy_count
                        # sku.sales = origin_sales + buy_count
                        # sku.save()
                        # 使用乐观锁修改sku数据
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=origin_stock - buy_count,
                                                                                 sales=origin_sales + buy_count)
                        if result == 0:
                            continue
                        # 修改spu数据
                        spu = SPU.objects.get(id=sku.spu_id)
                        origin_sales = spu.sales
                        # spu.sales = buy_count + origin_sales
                        # spu.save()
                        # 使用乐观锁修改数据库
                        SPU.objects.filter(id=sku.spu_id).update(sales=buy_count + origin_sales)
                        # 保存订单
                        OrderGoods.objects.create(
                            order_info=order_info,
                            sku_id=sku_id,
                            count=buy_count,
                            price=sku.price
                        )
                        order_info.total_amount += buy_count * sku.price
                        order_info.total_count += buy_count
                        break
                order_info.total_amount += order_info.freight
                order_info.save()
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)  # 下单失败，回滚到事物保存点
                return Response({'code': 400, 'errmsg': '下单失败'})
            else:
                transaction.savepoint_commit(save_id)  # 提交事物
        data = {
            'order_id': order_id,
            'total_amount': order_info.total_amount,
            'carts_count': order_info.total_count,
            "saller": "达达电商",
        }
        return Response({'code': 200, 'data': data})


