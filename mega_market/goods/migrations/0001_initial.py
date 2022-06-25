# Generated by Django 4.0.5 on 2022-06-25 20:01

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import goods.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ShopUnitCategory',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField(blank=True, default=None, editable=False, null=True, validators=[goods.models.equal_null])),
                ('type', models.CharField(default='CATEGORY', editable=False, max_length=20)),
                ('date', models.DateTimeField()),
                ('parent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goods.shopunitcategory')),
            ],
        ),
        migrations.CreateModel(
            name='ShopUnitOffer',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('price', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('type', models.CharField(default='OFFER', editable=False, max_length=20)),
                ('date', models.DateTimeField()),
                ('parent_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goods.shopunitcategory')),
            ],
        ),
    ]