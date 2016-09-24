# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flatpages', '0001_initial'),
        ('opendebates', '0028_auto_20160917_0853'),
    ]

    operations = [
        migrations.CreateModel(
            name='FlatPageMetadataOverride',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('facebook_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_WATCH-NOW_FB-1200x717-FODUrl.png')),
                ('facebook_description', models.TextField(default='Groundbreaking bottom-up #OpenDebate taking place NOW, hosted by Open Debate Coalition, Progressive Change Institute, & [MEDIA PARTNER]. All questions were chosen from top vote-getters online. WATCH LIVE HERE!')),
                ('facebook_title', models.TextField(default='WATCH NOW: [CANDIDATES] answer YOUR top-voted questions!')),
                ('twitter_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_WATCH-NOW_TW-1024x512-FODUrl.png')),
                ('twitter_description', models.TextField(default='WATCH NOW: Voters set the agenda for groundbreaking #OpenDebate.')),
                ('twitter_title', models.TextField(default='U.S. Senate candidates are answering YOUR questions!')),
                ('page', models.OneToOneField(to='flatpages.FlatPage')),
            ],
        ),
    ]
