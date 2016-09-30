# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0030_auto_20160927_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='effective_after',
            field=models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc), unique=True),
        ),
    ]
