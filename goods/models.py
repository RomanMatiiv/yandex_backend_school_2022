import uuid

from django.core.exceptions import ValidationError
from django.core.validators import BaseValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import CharField
from django.db.models import FloatField
from django.db.models import IntegerField
from django.db.models import UUIDField
from django.db.models import ForeignKey
from django.db.models import DateTimeField

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def equal_null(value):
    if value is not None:
        raise ValidationError("Must be None")


# def type_offer(value):
#     if value != ShopUnitType.OFFER:
#         raise ValidationError("Must be offer")
#
#
# def type_category(value):
#     if value != ShopUnitType.CATEGORY:
#         raise ValidationError("Must be category")


class ShopUnitType(models.TextChoices):
    OFFER = 'OFFER'
    CATEGORY = 'CATEGORY'


class ShopUnitOffer(models.Model):
    id = UUIDField(primary_key=True, editable=False)
    name = CharField(max_length=255, null=False)
    parent_id = ForeignKey('ShopUnitCategory', on_delete=models.CASCADE, null=True, blank=True)
    price = IntegerField(null=False, validators=[MinValueValidator(0)])
    type = CharField(max_length=20, default=ShopUnitType.OFFER, null=False, editable=False)
    date = DateTimeField()


class ShopUnitCategory(models.Model):
    id = UUIDField(primary_key=True, editable=False)
    name = CharField(max_length=255, null=False)
    parent_id = ForeignKey('ShopUnitCategory', on_delete=models.CASCADE, null=True, blank=True)
    price = IntegerField(null=True, blank=True, default=None, editable=False, validators=[equal_null])
    type = CharField(max_length=20, default=ShopUnitType.CATEGORY, null=False, editable=False)
    date = DateTimeField()



