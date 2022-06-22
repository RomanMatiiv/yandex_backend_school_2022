import json
import logging

from django.core.exceptions import ValidationError
from django.http import Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.exceptions import BadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from goods.models import ShopUnit


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ShopUnitApi(View):
    def post(self, request):
        body = json.loads(request.body)

        items = body.get('items')
        update_date = body.get('updateDate')
        all_shop_unit = {}
        for raw_shop_unit in items:
            uuid = raw_shop_unit.get('id')
            name = raw_shop_unit.get('name')
            price = raw_shop_unit.get('price')
            unit_type = raw_shop_unit.get('type')
            parent_id = raw_shop_unit.get('parentId')
            if parent_id: # todo тк порядок элементов произвольный может быть случай что родительский элемент добавится позже
                logger.debug(parent_id)
                try:
                    parent_id = ShopUnit.objects.get(pk=parent_id)
                except ShopUnit.DoesNotExist:
                    parent_id = all_shop_unit.get(parent_id)
                    if parent_id is None:
                        raise Http404

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
            except ValidationError as e:
                logger.error(shop_unit_data)
                logger.error(e)
                raise BadRequest('Validation Failed')
            else:
                all_shop_unit[uuid] = shop_unit

        logger.debug('start insert {} shop unit'.format(len(all_shop_unit)))

        for shop_unit in all_shop_unit.values():
            shop_unit.save()
        # ShopUnit.objects.bulk_create(all_shop_unit.values())
        # ShopUnit.objects.bulk_update(all_shop_unit.values(), fields=)

        data = {}
        return JsonResponse(data, status=200)
