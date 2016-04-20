# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0021_submission_local_votes'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='announcement_body',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='announcement_headline',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='announcement_link',
            field=models.URLField(null=True, blank=True),
        ),
    ]
