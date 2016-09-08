# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0023_sitemode_announcement_page_regex'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='banner_header_copy',
            field=models.CharField(default='Ask about the issues that are most important to you -- then vote for other important questions and encourage friends to do the same!', max_length=500),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='banner_header_title',
            field=models.CharField(default='Welcome to the Open Debate', max_length=255),
        ),
    ]
