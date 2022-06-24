import json
import logging
from uuid import UUID
from typing import Dict
from typing import List

from django.db import transaction
from django.db.models import Model

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

# from goods.models import ShopUnit
from goods.models import ShopUnitOffer
from goods.models import ShopUnitCategory
from goods.models import ShopUnitType


logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ShopUnitApi(View):

    def _items_json_to_model_with_meta(self, items: List[Dict], update_date: str) -> [Dict[ShopUnitOffer, UUID],
                                                                                      Dict[ShopUnitCategory, UUID]
                                                                                      ]:
        """
        Преобразует

        Внимание в моделях не заполнено поле parent_id
        тк не факт, что данные объекты уже есть в БД
        Args:
            items:
            update_date:

        Returns:

        """
        offer_items = {}
        category_items = {}

        for raw_shop_unit in items:
            try:
                uuid_unit = UUID(raw_shop_unit.get('id'))
                type_unit = raw_shop_unit.get('type')
                parent_id = raw_shop_unit.get('parentId')
                if parent_id:
                    parent_id = UUID(raw_shop_unit.get('parentId'))
            except ValueError:  # check UUID
                raise BadRequest('Validation Failed')

            unit_data_without_parent = {
                'id': uuid_unit,
                'name': raw_shop_unit.get('name'),
                'price': raw_shop_unit.get('price'),
                'type': type_unit,
                'date': update_date,
            }

            match type_unit:
                case ShopUnitType.OFFER:
                    shop_unit = ShopUnitOffer(**unit_data_without_parent)
                    offer_items[uuid_unit] = {'model': shop_unit,
                                              'parent_id': parent_id}
                case ShopUnitType.CATEGORY:
                    shop_unit = ShopUnitCategory(**unit_data_without_parent)
                    category_items[uuid_unit] = {'model': shop_unit,
                                                 'parent_id': parent_id}
                case _:
                    raise BadRequest('Validation Failed')

            try:
                shop_unit.clean_fields()
            except ValidationError as e:
                logger.error(e)
                raise BadRequest('Validation Failed')

        n_items = len(items)
        n_offer_items = len(offer_items)
        n_category_items = len(category_items)
        if n_items != n_offer_items + n_category_items:
            logger.debug("total: {}, offer:{}, category:{}".format(n_items, n_offer_items, n_category_items))
            # в одном запросе несколько элементов с одинаковым id
            raise BadRequest('Validation Failed')

        return [offer_items, category_items]

    # def _check_model_exist(self, items: Dict, unit_model, id_field='id') -> List[UUID]:
    #     all_uuid = items.keys()
    #     existing_shop_unit = unit_model.objects.filter(id__in=all_uuid).values_list(id_field, flat=True)
    #     # for uuid_unit in existing_shop_unit:
    #     #     items[uuid_unit]['exist'] = True
    #
    #     return existing_shop_unit

    def _separate_create_and_update(self, items, unit_model, id_field='id'):
        all_uuid = items.keys()
        existing_shop_unit = unit_model.objects.filter(id__in=all_uuid).values_list(id_field, flat=True)

        to_create = {}
        to_update = {}
        for uuid_unit, data in items.items():
            model = data['model']
            if uuid_unit in existing_shop_unit:
                to_update[uuid_unit] = model
            else:
                to_create[uuid_unit] = model

        return [to_create, to_update]

    def _fill_parent_shop_unit(self, items: Dict, old_items: Dict, unit_model):
        for uuid_unit, model in items.items():
            parent_id = old_items[uuid_unit]['parent_id']
            unit_parent = None
            if parent_id:
                try:
                    unit_parent = unit_model.objects.get(pk=parent_id)
                except unit_model.DoesNotExist:
                    raise BadRequest('Validation Failed')
            model.parent_id = unit_parent

        return items

    def post(self, request):
        body = json.loads(request.body)

        items = body.get('items')
        update_date = body.get('updateDate')
        offer_items, category_items = self._items_json_to_model_with_meta(items, update_date)

        create, update = self._separate_create_and_update(offer_items, ShopUnitOffer)
        offer_to_create_with_unfilled_parent = create
        offer_to_update_with_unfilled_parent = update

        create, update = self._separate_create_and_update(category_items, ShopUnitCategory)
        category_to_create_with_unfilled_parent = create
        category_to_update_with_unfilled_parent = update

        with transaction.atomic():
            # создаем и обновляем объекты не заполня родителей
            ShopUnitOffer.objects.bulk_create(offer_to_create_with_unfilled_parent.values(),)
            ShopUnitCategory.objects.bulk_create(category_to_create_with_unfilled_parent.values())
            ShopUnitOffer.objects.bulk_update(offer_to_update_with_unfilled_parent.values(), fields=['name', 'price', 'date'])
            ShopUnitCategory.objects.bulk_update(category_to_update_with_unfilled_parent.values(), fields=['name', 'price', 'date'])

            # заполняем родителей
            offer_with_parent = {}
            offer_with_parent.update(offer_to_create_with_unfilled_parent)
            offer_with_parent.update(offer_to_update_with_unfilled_parent)
            offer_with_parent = self._fill_parent_shop_unit(offer_with_parent, offer_items, ShopUnitCategory)
            category_with_parent = {}
            category_with_parent.update(category_to_create_with_unfilled_parent)
            category_with_parent.update(category_to_update_with_unfilled_parent)
            category_with_parent = self._fill_parent_shop_unit(category_with_parent, category_items, ShopUnitCategory)

            ShopUnitOffer.objects.bulk_update(offer_with_parent.values(), fields=['parent_id'])
            ShopUnitCategory.objects.bulk_update(category_with_parent.values(), fields=['parent_id'])

        data = {}
        return JsonResponse(data, status=200)

    # def old_post(self, request):
    #
    #     # чтение сырых данных----------------------------------------
    #     body = json.loads(request.body)
    #
    #     items = body.get('items')
    #     update_date = body.get('updateDate')
    #     all_shop_unit = {}
    #     for raw_shop_unit in items:
    #         uuid = raw_shop_unit.get('id')
    #         shop_unit_data = {
    #             'data': {
    #                 'id': uuid,
    #                 'name': raw_shop_unit.get('name'),
    #                 'price': raw_shop_unit.get('price'),
    #                 'type': raw_shop_unit.get('type'),
    #                 'date': update_date,
    #             },
    #             'raw_parent_id': raw_shop_unit.get('parentId'),
    #         }
    #         all_shop_unit[uuid] = shop_unit_data
    #     # ----------------------------------------------------------
    #
    #
    #     # 3 списка объектов, 1)все, 2)что обновить 3)что создать----
    #     all_uuid = all_shop_unit.keys()
    #     try:
    #         existing_shop_unit = ShopUnit.objects.filter(id__in=all_uuid).values_list('id', flat=True)
    #     except ValidationError:
    #         raise BadRequest('Validation Failed')
    #     existing_shop_unit = [str(i) for i in existing_shop_unit]
    #
    #     to_create_unit = all_shop_unit.copy()
    #     to_update_unit = {}
    #     for uuid in existing_shop_unit:
    #         unit_to_update = to_create_unit.pop(uuid)
    #         to_update_unit[uuid] = unit_to_update
    #     # all_shop_unit - все объекты из запроса
    #     # to_create_unit - объекты которых нет в БД
    #     # to_update_unit - объекты которые нужно обновить (уже есть в БД)
    #     # ----------------------------------------------------------
    #
    #
    #     # объекты на создание, без родителей-----------------------
    #     _to_create_unit = []
    #     for uuid, val in to_create_unit.items():
    #         unit_data = val['data']
    #         unit_raw_parent_id = val['raw_parent_id']
    #
    #         # поверка на то, что указанный parent_id вообще существует!!!!!!!кажется, что лучше не здесь это делать
    #         if unit_raw_parent_id:
    #             try:
    #                 _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
    #             except ShopUnit.DoesNotExist:
    #                 parent_id = all_shop_unit.get(unit_raw_parent_id)
    #                 # если не None то пока нет, но скоро создадим
    #                 if parent_id is None:
    #                     raise BadRequest('Validation Failed')
    #         shop_unit = ShopUnit(**unit_data)
    #         try:
    #             shop_unit.clean_fields()
    #         except ValidationError as e:
    #             raise BadRequest('Validation Failed')
    #         _to_create_unit.append(shop_unit)
    #     # ----------------------------------------------------------
    #
    #
    #     # объекты на обновление, без родитлей-----------------------
    #     _to_update_unit = []
    #     for uuid, val in to_update_unit.items():
    #         unit_data = val['data']
    #         unit_raw_parent_id = val['raw_parent_id']
    #
    #         # поверка на то, что указанный parent_id вообще существует!!!!!!!кажется, что лучше не здесь это делать
    #         if unit_raw_parent_id:
    #             try:
    #                 _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
    #             except ShopUnit.DoesNotExist:
    #                 parent_id = all_shop_unit.get(unit_raw_parent_id)
    #                 # если не None то пока нет, но скоро создадим
    #                 if parent_id is None:
    #                     raise BadRequest('Validation Failed')
    #         shop_unit = ShopUnit(**unit_data)
    #         try:
    #             shop_unit.clean_fields()
    #         except ValidationError as e:
    #             raise BadRequest('Validation Failed')
    #         _to_update_unit.append(shop_unit)
    #     # ----------------------------------------------------------
    #
    #
    #     # создаем и обновляем объекты не заполня родителей---------
    #     ShopUnit.objects.bulk_create(_to_create_unit)
    #     ShopUnit.objects.bulk_update(_to_update_unit, fields=['name', 'price', 'date'])
    #     # ----------------------------------------------------------
    #
    #
    #     # объекты на создание С родителями--------------------------
    #     _to_create_unit_with_parent_id = []
    #     for uuid, val in to_create_unit.items():
    #         unit_data = val['data']
    #         unit_raw_parent_id = val['raw_parent_id']
    #
    #         if unit_raw_parent_id:
    #             try:
    #                 unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
    #                 unit_data['parent_id'] = unit_parent
    #             except ShopUnit.DoesNotExist:
    #                 logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
    #                 return JsonResponse({"message": "inconsistent"}, status=500)
    #             shop_unit = ShopUnit(**unit_data)
    #             try:
    #                 shop_unit.clean_fields()
    #             except ValidationError as e:
    #                 raise BadRequest('Validation Failed')
    #             _to_create_unit_with_parent_id.append(shop_unit)
    #     # ----------------------------------------------------------
    #
    #
    #     # объекты на обновление С родителями-----------------------
    #     _to_update_unit_with_parent_id = []
    #     for uuid, val in to_update_unit.items():
    #         unit_data = val['data']
    #         unit_raw_parent_id = val['raw_parent_id']
    #
    #         if unit_raw_parent_id:
    #             try:
    #                 unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
    #                 unit_data['parent_id'] = unit_parent
    #             except ShopUnit.DoesNotExist:
    #                 logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
    #                 return JsonResponse({"message": "inconsistent"}, status=500)
    #             shop_unit = ShopUnit(**unit_data)
    #             try:
    #                 shop_unit.clean_fields()
    #             except ValidationError as e:
    #                 raise BadRequest('Validation Failed')
    #             _to_update_unit_with_parent_id.append(shop_unit)
    #     # ----------------------------------------------------------
    #
    #
    #     # ----------------------------------------------------------
    #     ShopUnit.objects.bulk_update(_to_create_unit_with_parent_id, fields=['parent_id'])
    #     ShopUnit.objects.bulk_update(_to_update_unit_with_parent_id, fields=['parent_id'])
    #     # ----------------------------------------------------------
    #
    #     data = {}
    #     return JsonResponse(data, status=200)














# def post(self, request):
#     body = json.loads(request.body)
#
#     items = body.get('items')
#     update_date = body.get('updateDate')
#     all_shop_unit = {}
#     for raw_shop_unit in items:
#         uuid = raw_shop_unit.get('id')
#         shop_unit_data = {
#             'data': {
#                 'id': uuid,
#                 'name': raw_shop_unit.get('name'),
#                 'price': raw_shop_unit.get('price'),
#                 'type': raw_shop_unit.get('type'),
#                 'date': update_date,
#             },
#             'raw_parent_id': raw_shop_unit.get('parentId'),
#         }
#         all_shop_unit[uuid] = shop_unit_data
#
#     all_uuid = all_shop_unit.keys()
#     try:
#         existing_shop_unit = ShopUnit.objects.filter(id__in=all_uuid).values_list('id', flat=True)
#     except ValidationError:
#         raise BadRequest('Validation Failed')
#     existing_shop_unit = [str(i) for i in existing_shop_unit]
#
#     to_create_unit = all_shop_unit.copy()
#     to_update_unit = {}
#     for uuid in existing_shop_unit:
#         unit_to_update = to_create_unit.pop(uuid)
#         to_update_unit[uuid] = unit_to_update
#     # all_shop_unit - все объекты из запроса
#     # to_create_unit - объекты которых нет в БД
#     # to_update_unit - объекты которые нужно обновить (уже есть в БД)
#
#     _to_create_unit = []
#     for uuid, val in to_create_unit.items():
#         unit_data = val['data']
#         unit_raw_parent_id = val['raw_parent_id']
#
#         # поверка на то, что указанный parent_id вообще существует
#         if unit_raw_parent_id:
#             try:
#                 _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
#             except ShopUnit.DoesNotExist:
#                 parent_id = all_shop_unit.get(unit_raw_parent_id)
#                 # если не None то пока нет, но скоро создадим
#                 if parent_id is None:
#                     raise BadRequest('Validation Failed')
#         shop_unit = ShopUnit(**unit_data)
#         try:
#             shop_unit.clean_fields()
#         except ValidationError as e:
#             raise BadRequest('Validation Failed')
#         _to_create_unit.append(shop_unit)
#
#     _to_update_unit = []
#     for uuid, val in to_update_unit.items():
#         unit_data = val['data']
#         unit_raw_parent_id = val['raw_parent_id']
#
#         # поверка на то, что указанный parent_id вообще существует
#         if unit_raw_parent_id:
#             try:
#                 _ = ShopUnit.objects.get(pk=unit_raw_parent_id)
#             except ShopUnit.DoesNotExist:
#                 parent_id = all_shop_unit.get(unit_raw_parent_id)
#                 # если не None то пока нет, но скоро создадим
#                 if parent_id is None:
#                     raise BadRequest('Validation Failed')
#         shop_unit = ShopUnit(**unit_data)
#         try:
#             shop_unit.clean_fields()
#         except ValidationError as e:
#             raise BadRequest('Validation Failed')
#         _to_update_unit.append(shop_unit)
#
#     ShopUnit.objects.bulk_create(_to_create_unit)
#     ShopUnit.objects.bulk_update(_to_update_unit, fields=['name', 'price', 'date'])
#
#     _to_create_unit_with_parent_id = []
#     for uuid, val in to_create_unit.items():
#         unit_data = val['data']
#         unit_raw_parent_id = val['raw_parent_id']
#
#         if unit_raw_parent_id:
#             try:
#                 unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
#                 unit_data['parent_id'] = unit_parent
#             except ShopUnit.DoesNotExist:
#                 logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
#                 return JsonResponse({"message": "inconsistent"}, status=500)
#             shop_unit = ShopUnit(**unit_data)
#             try:
#                 shop_unit.clean_fields()
#             except ValidationError as e:
#                 raise BadRequest('Validation Failed')
#             _to_create_unit_with_parent_id.append(shop_unit)
#
#     _to_update_unit_with_parent_id = []
#     for uuid, val in to_update_unit.items():
#         unit_data = val['data']
#         unit_raw_parent_id = val['raw_parent_id']
#
#         if unit_raw_parent_id:
#             try:
#                 unit_parent = ShopUnit.objects.get(pk=unit_raw_parent_id)
#                 unit_data['parent_id'] = unit_parent
#             except ShopUnit.DoesNotExist:
#                 logger.error('inconsistent parent with id {} must be exist'.format(unit_raw_parent_id))
#                 return JsonResponse({"message": "inconsistent"}, status=500)
#             shop_unit = ShopUnit(**unit_data)
#             try:
#                 shop_unit.clean_fields()
#             except ValidationError as e:
#                 raise BadRequest('Validation Failed')
#             _to_update_unit_with_parent_id.append(shop_unit)
#
#     ShopUnit.objects.bulk_update(_to_create_unit_with_parent_id, fields=['parent_id'])
#     ShopUnit.objects.bulk_update(_to_update_unit_with_parent_id, fields=['parent_id'])
#
#     data = {}
#     return JsonResponse(data, status=200)
