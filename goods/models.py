import uuid

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CharField
from django.db.models import FloatField
from django.db.models import UUIDField
from django.db.models import ForeignKey
from django.db.models import DateTimeField


class ShopUnitType(models.TextChoices):
    OFFER = 'OFFER'
    CATEGORY = 'CATEGORY'


class ShopUnitOffer(models.Model):
    id = UUIDField(primary_key=True, editable=False)
    name = CharField(max_length=255, null=False)
    parent_id = ForeignKey('ShopUnitCategory', on_delete=models.CASCADE, null=True, blank=True)
    price = FloatField(null=False, validators=[MinValueValidator(0)])
    type = CharField(max_length=20, default=ShopUnitType.OFFER, null=False, editable=False)  # todo написать валидатор который будет проверять что тип равен нужному
    date = DateTimeField()


class ShopUnitCategory(models.Model):
    id = UUIDField(primary_key=True, editable=False)
    name = CharField(max_length=255, null=False)
    parent_id = ForeignKey('ShopUnitCategory', on_delete=models.CASCADE, null=True, blank=True)
    price = FloatField(null=True, blank=True, default=None, editable=False)
    type = CharField(max_length=20, default=ShopUnitType.CATEGORY, null=False, editable=False)  # todo написать валидатор который будет проверять что тип равен нужному
    date = DateTimeField()



