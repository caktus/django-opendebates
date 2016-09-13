# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0026_voter_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='inline_css',
            field=models.TextField(null=True, blank=True),
        ),
    ]
