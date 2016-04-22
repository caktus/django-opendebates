# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0022_auto_20160420_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='announcement_page_regex',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
