import uuid

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


class ShopUnit(models.Model):
    id = UUIDField(primary_key=True, editable=False)
    name = CharField(max_length=255)
    parent_id = ForeignKey('ShopUnit', on_delete=models.CASCADE, null=True, blank=True)
    price = FloatField(null=True, blank=True,validators=[MinValueValidator(0)])   # todo для товаров не может быть NULL
    type = CharField(max_length=20, choices=ShopUnitType.choices)
    date = DateTimeField()
