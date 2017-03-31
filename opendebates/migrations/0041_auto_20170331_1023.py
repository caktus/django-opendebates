# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0040_auto_20170330_1101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topsubmissioncategory',
            options={'verbose_name_plural': 'top submission categories'},
        ),
    ]
