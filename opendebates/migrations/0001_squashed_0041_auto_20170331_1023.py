# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import caching.base
import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.migrations.operations.special
import django.db.models.deletion
import localflavor.us.models


# Note: this file is a squashed merge of all of the migrations in the opendebates/
# app on 2019-10-02. On a technical note, it's not actually the exact code of
# squashing the migrations, since the Django-generated squash wouldn't run. Instead,
# a few things have been updated (for example, instead of creating a SiteMode
# model, then renaming it to Debate (which caused issues when running the squashed
# migration, this migration just creates a Debate model).


def lookup_voter_from_user(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Submission = apps.get_model("opendebates", "Submission")
    for submission in Submission.objects.all():
        submission.voter = submission.user.voter
        submission.save()


def backfill_moderated(apps, schema_editor):
    Submission = apps.get_model('opendebates', 'Submission')
    qs = Submission.objects.filter(
        moderated_at__isnull=True
    ).filter(
        models.Q(approved=False) | models.Q(duplicate_of__isnull=False)
    ).annotate(last_vote=models.Max('vote__created_at'))
    for s in qs:
        s.moderated_at = s.last_vote
        s.save()

    # Deal with merged Submissions whose Votes have been moved
    qs = Submission.objects.filter(
        moderated_at__isnull=True
    ).filter(
        duplicate_of__isnull=False
    ).annotate(last_vote=models.Max('votes_merged_elsewhere__created_at'))
    for s in qs:
        s.moderated_at = s.last_vote
        s.save()

    # Deal with the stragglers
    qs = Submission.objects.filter(moderated_at__isnull=True)
    for s in qs:
        s.moderated_at = s.created_at
        s.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('flatpages', '0001_initial'),
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Voter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('zip', models.CharField(db_index=True, max_length=10)),
                ('state', models.CharField(blank=True, max_length=255, null=True)),
                ('source', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('display_name', models.CharField(blank=True, max_length=255, null=True)),
                ('twitter_handle', models.CharField(blank=True, max_length=255, null=True)),
                ('unsubscribed', models.BooleanField(default=False)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idea', models.TextField()),
                ('headline', models.TextField(blank=True, null=True)),
                ('followup', models.TextField(blank=True, null=True)),
                ('citation', models.URLField(blank=True, db_index=True, null=True, verbose_name=b'Optional link to full proposal or reference')),
                ('citation_verified', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(db_index=True)),
                ('ip_address', models.CharField(db_index=True, max_length=255)),
                ('editors_pick', models.BooleanField(default=False)),
                ('moderated', models.BooleanField(default=False)),
                ('has_duplicates', models.BooleanField(default=False)),
                ('votes', models.IntegerField(db_index=True, default=0)),
                ('score', models.FloatField(db_index=True, default=0)),
                ('rank', models.FloatField(db_index=True, default=0)),
                ('random_id', models.FloatField(db_index=True, default=0)),
                ('keywords', models.TextField(blank=True, null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opendebates.Category')),
                ('duplicate_of', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='duplicates', to='opendebates.Submission')),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.CharField(db_index=True, max_length=255)),
                ('request_headers', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(db_index=True)),
                ('original_merged_submission', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='votes_merged_elsewhere', to='opendebates.Submission')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opendebates.Submission')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opendebates.Voter')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('submission', 'voter')]),
        ),
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
        migrations.AddField(
            model_name='voter',
            name='first_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='voter',
            name='last_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='voter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='opendebates.Voter'),
        ),
        migrations.RunPython(lookup_voter_from_user),
        migrations.AlterField(
            model_name='submission',
            name='voter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opendebates.Voter'),
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=255, null=True)),
                ('last_name', models.CharField(blank=True, max_length=255, null=True)),
                ('current_title', models.CharField(blank=True, max_length=255, null=True)),
                ('bio', models.TextField(blank=True, default=b'', null=True)),
                ('website', models.URLField(blank=True, db_index=True, null=True)),
                ('facebook', models.URLField(blank=True, db_index=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('display_name', models.CharField(blank=True, help_text=b'Defaults to first_name last_name.', max_length=255, null=True)),
                ('twitter_handle', models.CharField(blank=True, max_length=16, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ZipCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zip', models.CharField(max_length=10, unique=True)),
                ('city', models.CharField(blank=True, max_length=255, null=True)),
                ('state', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='voter',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='voter', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='voter',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='voter',
            name='last_name',
        ),
        migrations.AddField(
            model_name='submission',
            name='source',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='source',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='submission',
            name='has_duplicates',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='submission',
            name='headline',
            field=models.TextField(default='An Important Question for our Candidates'),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reviewed', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='submission',
            name='moderated_removal',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='flag',
            name='duplicate_of',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='opendebates.Submission'),
        ),
        migrations.AddField(
            model_name='flag',
            name='to_remove',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='removal_flags', to='opendebates.Submission'),
        ),
        migrations.AddField(
            model_name='flag',
            name='voter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='opendebates.Voter'),
        ),
        migrations.AlterUniqueTogether(
            name='flag',
            unique_together=set([('to_remove', 'voter')]),
        ),
        migrations.AddField(
            model_name='flag',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='Debate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('show_question_votes', models.BooleanField(default=True)),
                ('show_total_votes', models.BooleanField(default=True)),
                ('allow_sorting_by_votes', models.BooleanField(default=True)),
                ('allow_voting_and_submitting_questions', models.BooleanField(default=True)),
                ('debate_time', models.DateTimeField(default=datetime.datetime(2099, 1, 1, 0, 0), help_text=b'Enter time that debate starts in timezone America/New_York')),
                ('debate_state', models.CharField(blank=True, max_length=5, null=True)),
                ('announcement_body', models.TextField(blank=True, null=True)),
                ('announcement_headline', models.CharField(blank=True, max_length=255, null=True)),
                ('announcement_link', models.URLField(blank=True, null=True)),
                ('announcement_page_regex', models.CharField(blank=True, max_length=255, null=True)),
                ('banner_header_copy', models.TextField(default='Ask about the issues that are most important to you -- then vote for other important questions and encourage friends to do the same!')),
                ('banner_header_title', models.TextField(default='Welcome to the<br>Open Debate')),
                ('popup_after_submission_text', models.TextField(default='Next, help your question collect votes. Share it on social media and email it to friends.')),
                ('email_body', models.TextField(default=b'Vote for my progressive idea for @OpenDebaters %(url)s')),
                ('email_subject', models.CharField(default=b'Vote for my progressive idea for @OpenDebaters', max_length=998)),
                ('facebook_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_VOTE-NOW_FB-1200x717-FODUrl.png')),
                ('facebook_question_description', models.TextField(default='"{idea}" At [TIME] on [DATE], [CANDIDATES] answer top vote-getting questions at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive Change Institute')),
                ('facebook_question_title', models.TextField(default='Click here to vote on this question for U.S. Senate candidates to answer at the #OpenDebate in [STATE]!')),
                ('facebook_site_description', models.TextField(default='Groundbreaking bottom-up #OpenDebate to take place [DATE] @[TIME], hosted by Open Debate Coalition, Progressive Change Institute, & [MEDIA PARTNER]. All questions will be chosen from top vote-getters online. Submit & vote here!')),
                ('facebook_site_title', models.TextField(default='HISTORIC: [CANDIDATES] answer YOUR top-voted questions!')),
                ('hashtag', models.CharField(default=b'DemOpenForum', max_length=255)),
                ('twitter_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_VOTE-NOW_TW-1024x512-FODUrl.png')),
                ('twitter_question_description', models.TextField(default='"{idea}" At [TIME] on [DAY, [CANDIDATES] answer top vote-getting questions at bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive Change Institute')),
                ('twitter_question_text_with_handle', models.TextField(default='Submit & vote on questions for #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst. h/t @{handle}')),
                ('twitter_question_text_no_handle', models.TextField(default='Submit & vote on questions for #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst.')),
                ('twitter_question_title', models.TextField(default='Click here to vote on this question for U.S. Senate candidates to answer at the #OpenDebate in Florida!')),
                ('twitter_site_description', models.TextField(default='[DATE] [TIME] on [TBD]: Voters set the agenda for groundbreaking #OpenDebate. Submit & vote here!')),
                ('twitter_site_text', models.TextField(default='Submit & vote on questions for the #OpenDebate hosted by Open Debate Coalition, Progressive Change Inst.')),
                ('twitter_site_title', models.TextField(default='U.S. Senate candidates answer YOUR questions!')),
                ('inline_css', models.TextField(blank=True)),
                ('previous_debate_time', models.DateTimeField(blank=True, help_text=b'Enter time that the previous debate occurred in timezone America/New_York to enable Votes Since Previous Debate sort option', null=True)),
            ],
            bases=(caching.base.CachingMixin, models.Model),
        ),
        migrations.AddField(
            model_name='submission',
            name='local_votes',
            field=models.IntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='voter',
            name='phone_number',
            field=localflavor.us.models.PhoneNumberField(blank=True, max_length=20),
        ),
        migrations.CreateModel(
            name='TopSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
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
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(unique=True)),
                ('title', models.TextField()),
                ('caption', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='opendebates.TopSubmissionCategory'),
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='submission',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='opendebates.Submission'),
        ),
        migrations.AddField(
            model_name='topsubmission',
            name='current_votes',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='topsubmission',
            unique_together=set([('category', 'submission')]),
        ),
        migrations.CreateModel(
            name='FlatPageMetadataOverride',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('facebook_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_WATCH-NOW_FB-1200x717-FODUrl.png')),
                ('facebook_description', models.TextField(default='Groundbreaking bottom-up #OpenDebate taking place NOW, hosted by Open Debate Coalition, Progressive Change Institute, & [MEDIA PARTNER]. All questions were chosen from top vote-getters online. WATCH LIVE HERE!')),
                ('facebook_title', models.TextField(default='WATCH NOW: [CANDIDATES] answer YOUR top-voted questions!')),
                ('twitter_image', models.URLField(default=b'https://s3.amazonaws.com/s3.boldprogressives.org/images/OpenDebates_WATCH-NOW_TW-1024x512-FODUrl.png')),
                ('twitter_description', models.TextField(default='WATCH NOW: Voters set the agenda for groundbreaking #OpenDebate.')),
                ('twitter_title', models.TextField(default='U.S. Senate candidates are answering YOUR questions!')),
                ('page', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='metadata', to='flatpages.FlatPage')),
            ],
        ),
        migrations.AlterField(
            model_name='submission',
            name='citation',
            field=models.URLField(blank=True, db_index=True, max_length=1024, null=True, verbose_name='Optional link to full proposal or reference'),
        ),
        migrations.AddField(
            model_name='submission',
            name='current_votes',
            field=models.IntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name='submission',
            name='moderated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_moderated),
        migrations.AddField(
            model_name='vote',
            name='is_invalid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='is_suspicious',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='sessionid',
            field=models.CharField(blank=True, default=b'', max_length=40),
        ),
        migrations.AddField(
            model_name='candidate',
            name='debate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='candidates', to='opendebates.Debate'),
        ),
        migrations.AddField(
            model_name='category',
            name='debate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='categories', to='opendebates.Debate'),
        ),
        migrations.AddField(
            model_name='topsubmissioncategory',
            name='debate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='top_categories', to='opendebates.Debate'),
        ),
        migrations.AddField(
            model_name='debate',
            name='site',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='site_modes', to='sites.Site'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='debate',
            name='prefix',
            field=models.SlugField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='debate',
            name='theme',
            field=models.CharField(choices=[(b'testing', b'testing'), (b'florida', b'florida')], default='testing', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='debate',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debates', to='sites.Site'),
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
        migrations.AlterModelOptions(
            name='topsubmissioncategory',
            options={'verbose_name_plural': 'top submission categories'},
        ),
    ]
