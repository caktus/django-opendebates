# -*- coding: utf-8 -*-
# Generated by Django 1.11.25 on 2019-10-04 10:46
from __future__ import unicode_literals

from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0004_on_delete_parameters'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='phone_number',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None),
        ),
    ]