# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0035_add_fraud_protection_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='sessionid',
            field=models.CharField(default=b'', max_length=40, blank=True),
        ),
    ]
