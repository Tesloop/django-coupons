# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-07-13 18:19
from __future__ import unicode_literals

import django.contrib.postgres.fields.citext
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('coupons', '0007_auto_20151105_2328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupon',
            name='code',
            field=django.contrib.postgres.fields.citext.CITextField(blank=True, help_text='Leaving this field empty will generate a random code.', max_length=30, unique=True, verbose_name='Code'),
        ),
    ]