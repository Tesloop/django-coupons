# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-26 19:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0010_coupon_multiple_uses'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='valid_from',
            field=models.DateTimeField(default=django.utils.timezone.now, help_text='Defaults to start right away', verbose_name='Valid from'),
        ),
    ]
