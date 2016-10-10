# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0032_make_current_votes_nonnullable'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='moderated_at',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
