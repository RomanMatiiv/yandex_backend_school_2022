import json
import logging

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render
from django.core.exceptions import BadRequest
from django.views import View

from goods.models import ShopUnit


logger = logging.getLogger(__name__)


class ShopUnitApi(View):
    def post(self, request):
        body = json.loads(request.body)

        items = body.get('items')
        update_date = body.get('updateDate')
        all_shop_unit = []
        for raw_shop_unit in items:
            uuid = raw_shop_unit.get('id')
            name = raw_shop_unit.get('name')
            parent_id = raw_shop_unit.get('parentId')
            price = raw_shop_unit.get('price')
            unit_type = raw_shop_unit.get('type')

            shop_unit_data = {
                'id': uuid,
                'name': name,
                'parent_id': parent_id,
                'price': price,
                'type': unit_type,
                'date': update_date,
            }
            shop_unit = ShopUnit(**shop_unit_data)
            try:
                shop_unit.clean_fields()
            except ValidationError:
                logger.error(shop_unit_data)
                BadRequest('Validation Failed')
            else:
                all_shop_unit.append(shop_unit)

        logger.debug('start insert {} shop unit'.format(len(all_shop_unit)))
        ShopUnit.objects.bulk_create(all_shop_unit)

        return JsonResponse(200)
