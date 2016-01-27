# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=255, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('subject', models.CharField(max_length=500)),
                ('html', models.TextField()),
                ('text', models.TextField()),
                ('from_email', models.CharField(max_length=255)),
                ('to_email', models.CharField(max_length=255)),
            ],
        ),
    ]
