# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0003_submission'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.CharField(max_length=255, db_index=True)),
                ('request_headers', models.TextField(null=True, blank=True)),
                ('created_at', models.DateTimeField(db_index=True)),
                ('original_merged_submission', models.ForeignKey(related_name='votes_merged_elsewhere', blank=True, to='opendebates.Submission', null=True)),
                ('submission', models.ForeignKey(to='opendebates.Submission')),
                ('voter', models.ForeignKey(to='opendebates.Voter')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('submission', 'voter')]),
        ),
    ]
