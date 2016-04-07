# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0017_enable_unaccent'),
    ]

    operations = [
        migrations.AddField(
            model_name='flag',
            name='note',
            field=models.TextField(null=True, blank=True),
        ),
    ]
