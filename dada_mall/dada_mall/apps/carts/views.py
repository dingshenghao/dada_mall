import json
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from django_redis import get_redis_connection

from dada_mall.utils.login_check import login_check
from goods.models import SKU, SPUSaleAttr
from user.models import User


class CartsView(APIView):
    """
    get: 查询购物车数据
    post: 添加购物车
    delete: 删除购物车数据
    put: 修改购物车数据
    """

    @login_check
    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'err': '数据出现错误'})
        redis_coon = get_redis_connection('default')
        redis_bytes_skus = redis_coon.hgetall('cart_%d' % user.id)
        # print(redis_bytes_skus)
        """
        sku_id : {'sku.id': sku_id, 'count': count}
        """
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
            carts.append(cart)
        return Response({'code': 200, 'data': carts, 'base_url': settings.PIC_URL})

    @login_check
    def post(self, request, username):
        sku_id = request.data['sku_id']
        count = request.data['count']
        dashop_count = request.data['dashop_count']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400})
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return Response({'code': 400})
        carts_count = int(dashop_count) + int(count)
        redis_coon = get_redis_connection('default')
        pl = redis_coon.pipeline()
        pl.hincrby('cart_%d' % user.id, sku_id, count)
        """
        sku_id_1: count; sku_id_2: count 
        """
        pl.sadd('is_select_%s' % username, sku.id)
        pl.execute()
        return Response({'code': 200, 'data': {'carts_count': carts_count}})

    @login_check
    def delete(self, request, username):
        query_dict = json.loads(request.body.decode())
        sku_id = query_dict['sku_id']
        redis_coon = get_redis_connection('default')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '数据错误！'})
        redis_coon.hdel('cart_%d' % user.id, sku_id)
        redis_bytes_skus = redis_coon.hgetall('cart_%d' % user.id)
        # print(redis_bytes_skus)
        """
        sku_id : {'sku.id': sku_id, 'count': count}
        """
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
            carts.append(cart)
        return Response({'code': 200, 'data': carts, 'base_url': settings.PIC_URL})

    @login_check
    def put(self, request, username):
        query_dict = json.loads(request.body.decode())
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'code': 400, 'error': '数据错误！'})
        redis_coon = get_redis_connection('default')
        pl = redis_coon.pipeline()
        sku_id = query_dict['sku_id']
        state = query_dict['state']
        if state == 'add':
            pl.hincrby('cart_%d' % user.id, sku_id, 1)
        if state == 'del':
            pl.hincrby('cart_%d' % user.id, sku_id, 1)
        if state == 'select':
            pl.sadd('is_select_%s' % username, sku_id)
        if state == 'unselect':
            pl.srem('is_select_%s' % username, sku_id)
        pl.execute()
        return Response({'code': 200})
