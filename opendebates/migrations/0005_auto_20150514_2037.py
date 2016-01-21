# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0004_auto_20150425_0556'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='moderated',
            new_name='approved',
        ),
        migrations.AlterField(
            model_name='submission',
            name='idea',
            field=models.TextField(verbose_name='Question'),
        ),
    ]
