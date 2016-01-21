# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0009_auto_20150714_0217'),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=255, null=True, blank=True)),
                ('last_name', models.CharField(max_length=255, null=True, blank=True)),
                ('current_title', models.CharField(max_length=255, null=True, blank=True)),
                ('bio', models.TextField(default=b'', null=True, blank=True)),
                ('website', models.URLField(db_index=True, null=True, blank=True)),
                ('facebook', models.URLField(db_index=True, null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('display_name', models.CharField(max_length=255, null=True, blank=True)),
                ('twitter_handle', models.CharField(max_length=16, null=True, blank=True)),
            ],
        ),
    ]
