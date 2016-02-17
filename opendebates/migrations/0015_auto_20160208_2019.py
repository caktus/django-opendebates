# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0014_auto_20160203_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='headline',
            field=models.TextField(default='An Important Question for our Candidates'),
            preserve_default=False,
        ),
    ]
