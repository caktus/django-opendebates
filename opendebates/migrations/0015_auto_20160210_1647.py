# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0014_auto_20160203_2029'),
    ]

    operations = [
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reviewed', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='submission',
            name='moderated_removal',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='flag',
            name='duplicate_of',
            field=models.ForeignKey(related_name='+', blank=True, to='opendebates.Submission', null=True),
        ),
        migrations.AddField(
            model_name='flag',
            name='to_remove',
            field=models.ForeignKey(related_name='removal_flags', to='opendebates.Submission'),
        ),
        migrations.AddField(
            model_name='flag',
            name='voter',
            field=models.ForeignKey(to='opendebates.Voter'),
        ),
        migrations.AlterUniqueTogether(
            name='flag',
            unique_together=set([('to_remove', 'voter')]),
        ),
    ]
