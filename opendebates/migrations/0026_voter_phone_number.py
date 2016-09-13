# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0025_move_site_theme_to_site_mode'),
    ]

    operations = [
        migrations.AddField(
            model_name='voter',
            name='phone_number',
            field=localflavor.us.models.PhoneNumberField(max_length=20, null=True, blank=True),
        ),
    ]
