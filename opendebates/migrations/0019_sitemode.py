# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import caching.base


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0018_flag_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteMode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('show_question_votes', models.BooleanField(default=True)),
                ('show_total_votes', models.BooleanField(default=True)),
                ('allow_sorting_by_votes', models.BooleanField(default=True)),
                ('allow_voting_and_submitting_questions', models.BooleanField(default=True)),
                ('debate_time', models.DateTimeField(default=datetime.datetime(2099, 1, 1, 0, 0), help_text=b'Enter time that debate starts in timezone America/New_York')),
            ],
            bases=(caching.base.CachingMixin, models.Model),
        ),
    ]
