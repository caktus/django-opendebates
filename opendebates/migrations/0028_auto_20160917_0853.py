# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0027_sitemode_inline_css'),
    ]

    operations = [
        migrations.CreateModel(
            name='TopSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('headline', models.TextField()),
                ('followup', models.TextField(blank=True)),
                ('votes', models.IntegerField()),
                ('rank', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TopSubmissionCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(unique=True)),
                ('title', models.TextField()),
                ('caption', models.CharField(max_length=255, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='category',
            field=models.ForeignKey(related_name='submissions', to='opendebates.TopSubmissionCategory'),
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, to='opendebates.Submission', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='topsubmission',
            unique_together=set([('category', 'submission')]),
        ),
    ]
