# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0020_sitemode_debate_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='local_votes',
            field=models.IntegerField(default=0, db_index=True),
        ),
    ]
