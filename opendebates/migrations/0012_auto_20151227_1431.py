# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0011_auto_20151123_1548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='voter',
            name='user',
            field=models.OneToOneField(related_name='voter', null=True, blank=True, to=settings.AUTH_USER_MODEL),
        ),
    ]
