# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0008_populate_submission_voter_from_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='submission',
            name='user',
        ),
        migrations.AlterField(
            model_name='submission',
            name='voter',
            field=models.ForeignKey(to='opendebates.Voter'),
        ),
    ]
