# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0030_auto_20160927_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='previous_debate_time',
            field=models.DateTimeField(help_text=b'Enter time that the previous debate occurred in timezone America/New_York to enable Votes Since Previous Debate sort option', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='current_votes',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='current_votes',
            field=models.IntegerField(null=True),
        ),
    ]
