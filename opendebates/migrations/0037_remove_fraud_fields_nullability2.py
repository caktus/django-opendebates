# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0036_remove_fraud_fields_nullability'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='is_suspicious',
            field=models.BooleanField(default=False),
        ),
    ]
