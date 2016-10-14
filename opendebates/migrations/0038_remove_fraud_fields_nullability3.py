# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0037_remove_fraud_fields_nullability2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vote',
            name='is_invalid',
            field=models.BooleanField(default=False),
        ),
    ]
