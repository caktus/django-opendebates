# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0019_sitemode'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='debate_state',
            field=models.CharField(max_length=5, null=True, blank=True),
        ),
    ]
