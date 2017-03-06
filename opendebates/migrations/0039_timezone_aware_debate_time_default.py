# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import opendebates.models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0038_remove_fraud_fields_nullability3'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitemode',
            name='debate_time',
            field=models.DateTimeField(default=opendebates.models.one_hundred_years, help_text=b'Enter time that debate starts in timezone America/New_York'),
        ),
    ]
