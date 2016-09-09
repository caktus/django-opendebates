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
            field=models.TextField(default='Ask about the issues that are most important to you -- then vote for other important questions and encourage friends to do the same!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='banner_header_title',
            field=models.TextField(default='Welcome to the<br>Open Debate'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='popup_after_submission_text',
            field=models.TextField(default='Next, help your question collect votes. Share it on social media and email it to friends.'),
        ),
    ]
