import json
import logging

from django.core.exceptions import ValidationError
from django.http import Http404
from django.http import HttpResponse
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
            shop_unit_data = {
                'data': {
                    'id': uuid,
                    'name': raw_shop_unit.get('name'),
                    'price': raw_shop_unit.get('price'),
                    'type': raw_shop_unit.get('type'),
                    'date': update_date,
                },
                'raw_parent_id': raw_shop_unit.get('parentId'),
            }
            all_shop_unit[uuid] = shop_unit_data

        all_uuid = all_shop_unit.keys()
        try:
            existing_shop_unit = ShopUnit.objects.filter(id__in=all_uuid).values_list('id', flat=True)
        except ValidationError:
            raise BadRequest('Validation Failed')
        existing_shop_unit = [str(i) for i in existing_shop_unit]

        to_create_unit = all_shop_unit.copy()
        to_update_unit = {}
        for uuid in existing_shop_unit:
            unit_to_update = to_create_unit.pop(uuid)
            to_update_unit[uuid] = unit_to_update
        # all_shop_unit - все объекты из запроса
        # to_create_unit - объекты которых нет в БД
        # to_update_unit - объекты которые нужно обновить (уже есть в БД)

        _to_create_unit = []
        for uuid, val in to_create_unit.items():
            unit_data = val['data']
            unit_raw_parent_id = val['raw_parent_id']

            # поверка на то, что указанный parent_id вообще существует
            if unit_raw_parent_id:
                try:
                    _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
                except ShopUnit.DoesNotExist:
                    parent_id = all_shop_unit.get(unit_raw_parent_id)
                    # если не None то пока нет, но скоро создадим
                    if parent_id is None:
                        raise BadRequest('Validation Failed')
            shop_unit = ShopUnit(**unit_data)
            try:
                shop_unit.clean_fields()
            except ValidationError as e:
                raise BadRequest('Validation Failed')
            _to_create_unit.append(shop_unit)

        _to_update_unit = []
        for uuid, val in to_update_unit.items():
            unit_data = val['data']
            unit_raw_parent_id = val['raw_parent_id']

            # поверка на то, что указанный parent_id вообще существует
            if unit_raw_parent_id:
                try:
                    _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
                except ShopUnit.DoesNotExist:
                    parent_id = all_shop_unit.get(unit_raw_parent_id)
                    # если не None то пока нет, но скоро создадим
                    if parent_id is None:
                        raise BadRequest('Validation Failed')
            shop_unit = ShopUnit(**unit_data)
            try:
                shop_unit.clean_fields()
            except ValidationError as e:
                raise BadRequest('Validation Failed')
            _to_update_unit.append(shop_unit)

        ShopUnit.objects.bulk_create(_to_create_unit)
        ShopUnit.objects.bulk_update(_to_update_unit, fields=['name', 'price', 'date'])

        _to_create_unit_with_parent_id = []
        for uuid, val in to_create_unit.items():
            unit_data = val['data']
            unit_raw_parent_id = val['raw_parent_id']

            if unit_raw_parent_id:
                try:
                    unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
                    unit_data['parent_id'] = unit_parent
                except ShopUnit.DoesNotExist:
                    logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
                    return JsonResponse({"message": "inconsistent"}, status=500)
                shop_unit = ShopUnit(**unit_data)
                try:
                    shop_unit.clean_fields()
                except ValidationError as e:
                    raise BadRequest('Validation Failed')
                _to_create_unit_with_parent_id.append(shop_unit)

        _to_update_unit_with_parent_id = []
        for uuid, val in to_update_unit.items():
            unit_data = val['data']
            unit_raw_parent_id = val['raw_parent_id']

            if unit_raw_parent_id:
                try:
                    unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
                    unit_data['parent_id'] = unit_parent
                except ShopUnit.DoesNotExist:
                    logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
                    return JsonResponse({"message": "inconsistent"}, status=500)
                shop_unit = ShopUnit(**unit_data)
                try:
                    shop_unit.clean_fields()
                except ValidationError as e:
                    raise BadRequest('Validation Failed')
                _to_update_unit_with_parent_id.append(shop_unit)

        ShopUnit.objects.bulk_update(_to_create_unit_with_parent_id, fields=['parent_id'])
        ShopUnit.objects.bulk_update(_to_update_unit_with_parent_id, fields=['parent_id'])

        data = {}
        return JsonResponse(data, status=200)
