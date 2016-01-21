# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0010_candidate'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZipCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('zip', models.CharField(unique=True, max_length=10)),
                ('city', models.CharField(max_length=255, null=True, blank=True)),
                ('state', models.CharField(max_length=255, null=True, blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='candidate',
            name='display_name',
            field=models.CharField(help_text=b'Defaults to first_name last_name.', max_length=255, null=True, blank=True),
        ),
    ]
