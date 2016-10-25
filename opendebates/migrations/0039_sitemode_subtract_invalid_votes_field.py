# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0038_remove_fraud_fields_nullability3'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='subtract_invalid_votes',
            field=models.PositiveIntegerField(default=0, help_text=b'Enter in the number of known invalid votes (that have not been explicitly marked as such directly) to remove them from the site-wide total.'),
        ),
    ]
