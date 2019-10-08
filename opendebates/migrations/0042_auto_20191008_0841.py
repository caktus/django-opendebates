# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0041_auto_20170331_1023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='debate',
            name='prefix',
            field=models.SlugField(default=b'', blank=True),
        ),
    ]
