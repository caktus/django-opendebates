# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import caching.base


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('opendebates', '0039_site_mode_fks'),
    ]

    operations = [
        migrations.RenameField(
            model_name='candidate',
            old_name='site_mode',
            new_name='debate',
        ),
        migrations.RenameField(
            model_name='category',
            old_name='site_mode',
            new_name='debate',
        ),
        migrations.RenameField(
            model_name='topsubmissioncategory',
            old_name='site_mode',
            new_name='debate',
        ),
        migrations.RenameModel(
            old_name='SiteMode',
            new_name='Debate',
        ),
        migrations.AlterField(
            model_name='debate',
            name='site',
            field=models.ForeignKey(related_name='debates', to='sites.Site'),
        ),
        migrations.AlterField(
            model_name='candidate',
            name='debate',
            field=models.ForeignKey(related_name='candidates', to='opendebates.Debate'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='debate',
            field=models.ForeignKey(related_name='categories', to='opendebates.Debate'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='topsubmissioncategory',
            name='debate',
            field=models.ForeignKey(related_name='top_categories', to='opendebates.Debate'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='topsubmissioncategory',
            name='slug',
            field=models.SlugField(),
        ),
        migrations.AlterUniqueTogether(
            name='topsubmissioncategory',
            unique_together=set([('debate', 'slug')]),
        ),
    ]
