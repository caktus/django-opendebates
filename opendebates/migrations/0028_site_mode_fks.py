# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('opendebates', '0027_sitemode_inline_css'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidate',
            name='site_mode',
            field=models.ForeignKey(related_name='candidates', default=1, to='opendebates.SiteMode'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='site_mode',
            field=models.ForeignKey(related_name='categories', default=1, to='opendebates.SiteMode'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sitemode',
            name='site',
            field=models.OneToOneField(related_name='site_mode', default=1, to='sites.Site'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sitemode',
            name='theme',
            field=models.CharField(default='testing', max_length=255, choices=[(b'testing', b'testing'), (b'florida', b'florida')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='voter',
            name='site_mode',
            field=models.ForeignKey(related_name='voters', default=1, to='opendebates.SiteMode'),
            preserve_default=False,
        ),
    ]
