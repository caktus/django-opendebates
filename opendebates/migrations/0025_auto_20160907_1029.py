# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0024_auto_20160907_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sitemode',
            name='banner_header_copy',
            field=models.TextField(default='Ask about the issues that are most important to you -- then vote for other important questions and encourage friends to do the same!'),
        ),
        migrations.AlterField(
            model_name='sitemode',
            name='banner_header_title',
            field=models.TextField(default='Welcome to the\nOpen Debate'),
        ),
    ]
