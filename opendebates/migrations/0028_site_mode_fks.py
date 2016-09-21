# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
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
            name='domain',
            field=models.CharField(default=1, unique=True, max_length=100, verbose_name='domain name'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sitemode',
            name='theme',
            field=models.CharField(default=1, max_length=255, choices=[(b'testing', b'testing'), (b'florida', b'florida')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='voter',
            name='site_mode',
            field=models.ForeignKey(related_name='voters', default=1, to='opendebates.SiteMode'),
            preserve_default=False,
        ),
    ]
