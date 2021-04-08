from django.conf import settings

from .models import SKU, Catalog, SPU, SaleAttrValue, SPUSaleAttr
from rest_framework.views import APIView
from rest_framework.response import Response


class GoodsIndexView(APIView):
    """
    get: 首页数据展示
    """

    def get(self, request):
        all_catalog = Catalog.objects.all()
        res = []
        for catalog in all_catalog:
            cata_dict = {}
            cata_dict['catalog_id'] = catalog.id
            cata_dict['catalog_name'] = catalog.name
            spu_ids = SPU.objects.filter(catalog_id=catalog.id).values("id")
            sku_list = SKU.objects.filter(spu_id__in=spu_ids, is_launched=True)[:3]
            cata_dict["sku"] = []
            for sku in sku_list:
                sku_dict = {}
                sku_dict["skuid"] = sku.id
                sku_dict["name"] = sku.name
                sku_dict["caption"] = sku.caption
                # 将金额类数据转成字符串
                sku_dict["price"] = str(sku.price)
                # str(image字段)会返回该字段的值,否则返回image对象
                sku_dict["image"] = str(sku.default_image_url)
                cata_dict["sku"].append(sku_dict)
            res.append(cata_dict)
        return Response({"code": 200, "data": res, "base_url": settings.PIC_URL})


class GoodsDetailView(APIView):

    def get(self, request, id):
        try:
            sku = SKU.objects.get(id=id)
        except SKU.DoesNotExist:
            return Response({'code': 400, 'error': '没有数据！'})
        spu = SPU.objects.get(id=sku.id)
        catalog = Catalog.objects.get(id=spu.catalog_id)
        sku_sale_attr_names = []
        sku_sale_attr_id = []
        attrs = SPUSaleAttr.objects.filter(spu_id=spu.id)
        for attr in attrs:
            sku_sale_attr_names.append(attr.name)
            sku_sale_attr_id.append(attr.id)
        sku_sale_attr_val_id = [i.id for i in sku.sale_attr_value.all()]
        sku_all_sale_attr_vals_id = {}
        sku_all_sale_attr_vals_name = {}
        for id in sku_sale_attr_val_id:
            items = SaleAttrValue.objects.filter(spu_sale_attr_id=id)
            sku_all_sale_attr_vals_id[id] = []
            sku_all_sale_attr_vals_name[id] = []
            for item in items:
                sku_all_sale_attr_vals_id[id].append(item.id)
                sku_all_sale_attr_vals_name[id].append(item.name)
        data = {
            'catalog_id': catalog.id,
            'catalog_name': catalog.name,
            'name': sku.name,
            'image': str(sku.default_image_url),
            'caption': sku.caption,
            'price': str(sku.price),
            'spu': spu.id,
            'sku_sale_attr_names': sku_sale_attr_names,
            'sku_sale_attr_id': sku_sale_attr_id,
            'sku_sale_attr_val_id': sku_sale_attr_val_id,
            'sku_all_sale_attr_vals_id': sku_all_sale_attr_vals_id,
            'sku_all_sale_attr_vals_name': sku_all_sale_attr_vals_name
        }
        return Response({'code': 200, 'data': data, 'base_url': settings.PIC_URL})