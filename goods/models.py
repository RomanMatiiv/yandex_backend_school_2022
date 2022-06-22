import uuid

from django.core.exceptions import ValidationError
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
    price = FloatField(null=True, blank=True, validators=[MinValueValidator(0)])   # todo для товаров не может быть NULL
    type = CharField(max_length=20, choices=ShopUnitType.choices, editable=False)  # todo не работает eidtable=False
    date = DateTimeField()

    def clean_fields(self, exclude=None):
        if self.type == ShopUnitType.OFFER:
            if self.price is None:
                error = {'price': "ShopUnit with type: {} must be not null".format(ShopUnitType.OFFER)}
                raise ValidationError(error)

        return super().clean_fields(exclude)




