# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('opendebates', '0024_auto_20160909_1025'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitemode',
            name='email_body',
            field=models.TextField(default=b'Vote for my progressive idea for @OpenDebaters %(url)s'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='email_subject',
            field=models.CharField(default=b'Vote for my progressive idea for @OpenDebaters', max_length=998),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='facebook_image',
            field=models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_VOTE-NOW_FB-1200x717-FODUrl.png'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='facebook_question_description',
            field=models.TextField(default='"{idea}" At [TIME] on [DATE], [CANDIDATES] answer top vote-getting questions at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive Change Institute'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='facebook_question_title',
            field=models.TextField(default='Click here to vote on this question for U.S. Senate candidates to answer at the #OpenDebate in [STATE]!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='facebook_site_description',
            field=models.TextField(default='Groundbreaking bottom-up #OpenDebate to take place [DATE] @[TIME], hosted by Open Debate Coalition, Progressive Change Institute, & [MEDIA PARTNER]. All questions will be chosen from top vote-getters online. Submit & vote here!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='facebook_site_title',
            field=models.TextField(default='HISTORIC: [CANDIDATES] answer YOUR top-voted questions!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='hashtag',
            field=models.CharField(default=b'DemOpenForum', max_length=255),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_image',
            field=models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_VOTE-NOW_TW-1024x512-FODUrl.png'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_question_description',
            field=models.TextField(default='"{idea}" At [TIME] on [DAY, [CANDIDATES] answer top vote-getting questions at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive Change Institute'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_question_text_with_handle',
            field=models.TextField(default='Submit & vote on questions for #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst.'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_question_text_no_handle',
            field=models.TextField(default='Submit & vote on questions for #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst.'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_question_title',
            field=models.TextField(default='Click here to vote on this question for U.S. Senate candidates to answer at the #OpenDebate in Florida!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_site_description',
            field=models.TextField(default='[DATE] [TIME] on [TBD]: Voters set the agenda for groundbreaking #OpenDebate. Submit & vote here!'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_site_text',
            field=models.TextField(default='Submit & vote on questions for the #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst.'),
        ),
        migrations.AddField(
            model_name='sitemode',
            name='twitter_site_title',
            field=models.TextField(default='U.S. Senate candidates answer YOUR questions!'),
        ),
    ]
