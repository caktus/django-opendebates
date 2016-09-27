# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0029_flatpagemetadataoverride'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submission',
            name='citation',
            field=models.URLField(db_index=True, max_length=1024, null=True, verbose_name='Optional link to full proposal or reference', blank=True),
        ),
    ]
