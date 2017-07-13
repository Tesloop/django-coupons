# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.contrib.postgres.operations import CITextExtension
from django.contrib.postgres.fields import CITextField


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0007_auto_20151105_2328'),
    ]

    operations = [
        CITextExtension(),
        migrations.AlterField(
            model_name='coupon',
            name='code',
            field=CITextField(max_length=30, unique=True, blank=True),
        ),
    ]

