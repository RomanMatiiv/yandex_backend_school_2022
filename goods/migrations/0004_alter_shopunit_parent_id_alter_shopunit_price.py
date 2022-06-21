# Generated by Django 4.0.5 on 2022-06-21 16:33

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0003_alter_shopunit_parent_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shopunit',
            name='parent_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='goods.shopunit'),
        ),
        migrations.AlterField(
            model_name='shopunit',
            name='price',
            field=models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
