# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgfulltext.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('opendebates', '0002_voter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('idea', models.TextField()),
                ('headline', models.TextField(null=True, blank=True)),
                ('followup', models.TextField(null=True, blank=True)),
                ('citation', models.URLField(db_index=True, null=True, verbose_name=b'Optional link to full proposal or reference', blank=True)),
                ('citation_verified', models.BooleanField(default=False, db_index=True)),
                ('created_at', models.DateTimeField(db_index=True)),
                ('ip_address', models.CharField(max_length=255, db_index=True)),
                ('editors_pick', models.BooleanField(default=False)),
                ('moderated', models.BooleanField(default=False)),
                ('has_duplicates', models.BooleanField(default=False)),
                ('votes', models.IntegerField(default=0, db_index=True)),
                ('score', models.FloatField(default=0, db_index=True)),
                ('rank', models.FloatField(default=0, db_index=True)),
                ('random_id', models.FloatField(default=0, db_index=True)),
                ('search_index', djorm_pgfulltext.fields.VectorField()),
                ('keywords', models.TextField(null=True, blank=True)),
                ('category', models.ForeignKey(to='opendebates.Category')),
                ('duplicate_of', models.ForeignKey(related_name='duplicates', blank=True, to='opendebates.Submission', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
