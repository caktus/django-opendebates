# coding=utf-8
import datetime
from django.db import models
from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.sites.models import Site
from urllib import quote_plus
from django.utils.http import urlquote
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from caching.base import CachingManager, CachingMixin
from localflavor.us.models import PhoneNumberField

from opendebates import site_defaults

NUMBER_OF_VOTES_CACHE_ENTRY = 'number_of_votes-{}'
RECENT_EVENTS_CACHE_ENTRY = 'recent_events_cache_entry-{}'


class Category(CachingMixin, models.Model):

    debate = models.ForeignKey('Debate', related_name='categories')
    name = models.CharField(max_length=255)

    objects = CachingManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = _("categories")


class FlatPageMetadataOverride(models.Model):

    page = models.OneToOneField('flatpages.FlatPage', related_name='metadata')

    facebook_image = models.URLField(default=site_defaults.FLATPAGE_FACEBOOK_IMAGE)
    facebook_description = models.TextField(default=site_defaults.FLATPAGE_FACEBOOK_DESCRIPTION)
    facebook_title = models.TextField(default=site_defaults.FLATPAGE_FACEBOOK_TITLE)

    twitter_image = models.URLField(default=site_defaults.FLATPAGE_TWITTER_IMAGE)
    twitter_description = models.TextField(default=site_defaults.FLATPAGE_TWITTER_DESCRIPTION)
    twitter_title = models.TextField(default=site_defaults.FLATPAGE_TWITTER_TITLE)


class Debate(CachingMixin, models.Model):
    THEME_CHOICES = [(theme, theme) for theme in settings.SITE_THEMES]

    site = models.ForeignKey(Site, related_name='debates')
    prefix = models.SlugField()
    theme = models.CharField(max_length=255, choices=THEME_CHOICES)

    show_question_votes = models.BooleanField(default=True, blank=True)
    show_total_votes = models.BooleanField(default=True, blank=True)
    allow_sorting_by_votes = models.BooleanField(default=True, blank=True)
    allow_voting_and_submitting_questions = models.BooleanField(default=True, blank=True)
    debate_time = models.DateTimeField(
        default=datetime.datetime(2099, 1, 1),
        help_text="Enter time that debate starts in timezone %s" % settings.TIME_ZONE,
    )
    debate_state = models.CharField(max_length=5, null=True, blank=True)
    previous_debate_time = models.DateTimeField(
        null=True, blank=True,
        help_text=(
            "Enter time that the previous debate occurred in timezone %s"
            " to enable Votes Since Previous Debate sort option" % settings.TIME_ZONE)
    )

    inline_css = models.TextField(blank=True)

    announcement_headline = models.CharField(max_length=255, null=True, blank=True)
    announcement_body = models.TextField(null=True, blank=True)
    announcement_link = models.URLField(null=True, blank=True)
    announcement_page_regex = models.CharField(max_length=255, null=True, blank=True)

    hashtag = models.CharField(default=site_defaults.HASHTAG, max_length=255)

    banner_header_title = models.TextField(default=site_defaults.BANNER_HEADER_TITLE)
    banner_header_copy = models.TextField(default=site_defaults.BANNER_HEADER_COPY)

    popup_after_submission_text = models.TextField(
        default=site_defaults.POPUP_AFTER_SUBMISSION_TEXT,
    )

    email_subject = models.CharField(default=site_defaults.EMAIL_SUBJECT, max_length=998)
    email_body = models.TextField(default=site_defaults.EMAIL_BODY)

    facebook_image = models.URLField(default=site_defaults.FACEBOOK_IMAGE)
    facebook_question_description = models.TextField(
        default=site_defaults.FACEBOOK_QUESTION_DESCRIPTION,
    )
    facebook_question_title = models.TextField(default=site_defaults.FACEBOOK_QUESTION_TITLE)
    facebook_site_description = models.TextField(default=site_defaults.FACEBOOK_SITE_DESCRIPTION)
    facebook_site_title = models.TextField(default=site_defaults.FACEBOOK_SITE_TITLE)

    twitter_image = models.URLField(default=site_defaults.TWITTER_IMAGE)
    twitter_question_description = models.TextField(
        default=site_defaults.TWITTER_QUESTION_DESCRIPTION,
    )
    twitter_question_text_with_handle = models.TextField(
        default=site_defaults.TWITTER_QUESTION_TEXT_WITH_HANDLE,
    )
    twitter_question_text_no_handle = models.TextField(
        default=site_defaults.TWITTER_QUESTION_TEXT_NO_HANDLE,
    )
    twitter_question_title = models.TextField(default=site_defaults.TWITTER_QUESTION_TITLE)
    twitter_site_description = models.TextField(default=site_defaults.TWITTER_SITE_DESCRIPTION)
    twitter_site_text = models.TextField(default=site_defaults.TWITTER_SITE_TEXT)
    twitter_site_title = models.TextField(default=site_defaults.TWITTER_SITE_TITLE)

    objects = CachingManager()

    def __unicode__(self):
        return u'/'.join([self.site.domain, self.prefix])


class SubmissionQuerySet(models.QuerySet):
    def search(self, term):
        return self.filter(search_vector=term)


class Submission(models.Model):
    # The _search_vectors are the search vectors used to update the search_vector
    # field whenever a Submission is saved.
    _search_vector_fields = ['idea', 'keywords']
    _search_vectors = SearchVector('idea', weight='A') + SearchVector('keywords', weight='A')

    def user_display_name(self):
        return self.voter.user_display_name()

    category = models.ForeignKey(Category)
    idea = models.TextField(verbose_name=_('Question'))

    headline = models.TextField(null=False, blank=False)
    followup = models.TextField(null=True, blank=True)

    citation = models.URLField(null=True, blank=True, db_index=True,
                               max_length=1024,
                               verbose_name=_("Optional link to full proposal or reference"))
    citation_verified = models.BooleanField(default=False, db_index=True)

    voter = models.ForeignKey("Voter")
    created_at = models.DateTimeField(db_index=True)
    moderated_at = models.DateTimeField(blank=True, null=True)

    ip_address = models.CharField(max_length=255, db_index=True)

    editors_pick = models.BooleanField(default=False)
    approved = models.BooleanField(default=False, db_index=True)

    # if True, will not show up again in moderation list.
    moderated_removal = models.BooleanField(default=False, db_index=True)

    has_duplicates = models.BooleanField(default=False, db_index=True)

    duplicate_of = models.ForeignKey('opendebates.Submission', null=True, blank=True,
                                     related_name="duplicates")

    votes = models.IntegerField(default=0, db_index=True)
    local_votes = models.IntegerField(default=0, db_index=True)
    current_votes = models.IntegerField(default=0, db_index=True)
    score = models.FloatField(default=0, db_index=True)
    rank = models.FloatField(default=0, db_index=True)

    random_id = models.FloatField(default=0, db_index=True)

    # A field in the database that is used when searching this model. Instead of
    # searching all of the relevant fields each time a user searches, we prepopulate
    # the search_vector field (based on Submission._search_vectors) anytime a
    # Submission is saved, and index the database table on this field, for faster
    # retrieval.
    search_vector = SearchVectorField(null=True)

    keywords = models.TextField(null=True, blank=True)

    # Use the SubmissionQuerySet, so we get the .search() method, which is expected
    # in other parts of the application.
    objects = SubmissionQuerySet.as_manager()

    source = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(fields=['search_vector'])
        ]

    @property
    def debate(self):
        # avoid lots of unneeded round trips to memcached in production by
        # allowing this cached attribute to be set via the {% provide_site_to %}
        # template tag
        if not hasattr(self, '_cached_debate'):
            self._cached_debate = self.category.debate
        return self._cached_debate

    def save(self, *args, **kwargs):
        """
        Update the search_vector field whenever the save() method is called.

        Note: ideally, instead of updating the search_vector field from the save()
        method, we would prefer to use a stored generated column (see
        https://www.postgresql.org/docs/12/ddl-generated-columns.html), and let
        Postgres handle updating its value on its own. However, this feature only
        becomes available on Postgres 12, which we are not using yet. Perhaps we
        can use that feature when we upgrade to Postgres 12 in the future.
        """
        # If the search_vector field was updated, then we do not need to update it here.
        search_vector_updated = False
        if kwargs.get('search_vector_updated', False):
            search_vector_updated = kwargs.pop('search_vector_updated')

        super(Submission, self).save(*args, **kwargs)

        # Determine if we need to update the search_vector field.
        updating_all_fields = 'update_fields' not in kwargs
        need_to_update_search_vector = (
            not search_vector_updated and
            (
                updating_all_fields or
                any(
                    [
                        kwargs['update_fields'].count(vector_field_name)
                        for vector_field_name in self._search_vector_fields
                    ]
                )
            )
        )
        if need_to_update_search_vector:
            self.search_vector = self._search_vectors
            # Set the search_vector_updated kwarg, so we avoid an infinite loop
            # or search_vector updates.
            self.save(search_vector_updated=True)

    def get_recent_votes(self):
        timespan = now() - datetime.timedelta(1)
        return Vote.objects.filter(submission=self, created_at__gte=timespan).count()

    def get_duplicates(self):
        if not self.has_duplicates:
            return None
        return Submission.objects.select_related(
            "voter", "category", "voter__user").filter(
            approved=True, duplicate_of=self)

    def __unicode__(self):
        return self.idea

    def get_absolute_url(self):
        # We are overriding the urlconf here so that the site-specific urlconf
        # is not used, and we can fully specify the site prefix.
        return reverse('vote', kwargs={'prefix': self.debate.prefix, 'id': self.id},
                       urlconf=settings.ROOT_URLCONF)

    def tweet_text(self):
        if self.voter.twitter_handle:
            text = self.debate.twitter_question_text_with_handle.format(
                handle=self.voter.twitter_handle,
            )
        else:
            text = self.debate.twitter_question_text_no_handle
        return text

    def facebook_text(self):
        if len(self.idea) > 240:
            return self.idea[:240] + u'…'
        return self.idea

    def facebook_url(self):
        return u"https://www.facebook.com/sharer/sharer.php?&u=%(idea_url)s" % {
            "idea_url": quote_plus(self.really_absolute_url('fb')),
            }

    def reddit_url(self):
        return u"//www.reddit.com/submit?url=%s" % (quote_plus(self.really_absolute_url('reddit')),)

    def email_url(self):
        subject = self.debate.email_subject
        body = self.debate.email_body % {
            "url": self.really_absolute_url('email'),
        }
        return u"mailto:?subject=%s&body=%s" % (urlquote(subject), urlquote(body))

    def sms_url(self):
        params = {
            "url": self.really_absolute_url('sms'),
            "hashtag": self.debate.hashtag,
        }
        body = _(u"Vote for my progressive idea for @OpenDebaters #%(hashtag)s. %(url)s" % params)
        return u"sms:;?body=%s" % (quote_plus(body),)

    def really_absolute_url(self, source=None):
        url = 'https://' + self.debate.site.domain + self.get_absolute_url()
        if source is not None:
            url += '?source=share-%s-%s' % (source, self.id)
        return url

    def twitter_url(self):
        url_tmpl = u"https://twitter.com/intent/tweet?url=" + \
                   "%(idea_url)s&text=%(tweet_text)s"
        return url_tmpl % {
            "idea_url": quote_plus(self.really_absolute_url('tw')),
            "tweet_text": quote_plus(self.tweet_text()),
            }

    def twitter_title(self):
        # Vote on this question for the FL-Sen #OpenDebate!
        return self.debate.twitter_question_title.format(idea=self.idea)

    def twitter_description(self):
        # "{idea}" At 8pm EDT on 4/25, Jolly & Grayson answer top vote-getting questions at
        # bottom-up #OpenDebate hosted by [TBD], Open Debate Coalition, Progressive Change Institute
        return self.debate.twitter_question_description.format(idea=self.idea)

    def facebook_title(self):
        return self.debate.facebook_question_title.format(idea=self.idea)

    def facebook_description(self):
        return self.debate.facebook_question_description.format(idea=self.idea)


class ZipCode(CachingMixin, models.Model):
    zip = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)

    objects = CachingManager()


class Voter(models.Model):

    def user_display_name(self):
        voter = self
        if voter.display_name:
            name = voter.display_name
        elif not voter.user:
            name = _(u"Somebody")
        else:
            user = voter.user
            name = u"%s" % user.first_name
            if user.last_name:
                name = u"%s %s." % (name, user.last_name[0])
        if not name or not name.strip():
            name = _(u"Somebody")

        if voter.state:
            name = _(u"%(name)s from %(state)s" % {"name": name, "state": voter.state})
        return name

    email = models.EmailField(unique=True)
    zip = models.CharField(max_length=10, db_index=True)
    state = models.CharField(max_length=255, null=True, blank=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, related_name="voter")

    source = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    display_name = models.CharField(max_length=255, null=True, blank=True)
    twitter_handle = models.CharField(max_length=255, null=True, blank=True)
    phone_number = PhoneNumberField(blank=True)

    unsubscribed = models.BooleanField(default=False)

    def __unicode__(self):
        return self.email

    def account_token(self):
        return Voter.make_account_token(self.email)

    @classmethod
    def make_account_token(cls, email):
        signer = Signer()
        value = signer.sign(email)
        return value


class Vote(models.Model):

    submission = models.ForeignKey(Submission)
    voter = models.ForeignKey(Voter)

    is_suspicious = models.BooleanField(default=False)
    is_invalid = models.BooleanField(default=False)

    ip_address = models.CharField(max_length=255, db_index=True)
    sessionid = models.CharField(max_length=40, blank=True, default='')
    request_headers = models.TextField(null=True, blank=True)

    original_merged_submission = models.ForeignKey(Submission, null=True, blank=True,
                                                   related_name="votes_merged_elsewhere")

    class Meta:
        unique_together = [("submission", "voter")]

    created_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=255, null=True, blank=True)


class Candidate(models.Model):
    debate = models.ForeignKey('Debate', related_name='candidates')

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    current_title = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(default='', null=True, blank=True)
    website = models.URLField(null=True, blank=True, db_index=True)
    facebook = models.URLField(null=True, blank=True, db_index=True)
    twitter_handle = models.CharField(max_length=16, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True,
                                    help_text=_("Defaults to first_name last_name."))

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = u'{0} {1}'.format(self.first_name, self.last_name)
        super(Candidate, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.display_name


class Flag(models.Model):
    to_remove = models.ForeignKey(Submission, related_name='removal_flags')
    duplicate_of = models.ForeignKey(Submission, related_name='+',
                                     null=True, blank=True)
    voter = models.ForeignKey(Voter)
    reviewed = models.BooleanField(default=False)
    note = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = [
            ('to_remove', 'voter'),
        ]


class TopSubmissionCategory(models.Model):
    debate = models.ForeignKey('Debate', related_name='top_categories')

    slug = models.SlugField()
    title = models.TextField()
    caption = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = _("top submission categories")
        unique_together = [('debate', 'slug')]

    def __unicode__(self):
        return self.slug


class TopSubmission(models.Model):
    category = models.ForeignKey(TopSubmissionCategory, related_name='submissions')
    submission = models.ForeignKey(Submission, null=True, blank=False,
                                   on_delete=models.SET_NULL)

    headline = models.TextField(null=False, blank=False)
    followup = models.TextField(null=False, blank=True)

    votes = models.IntegerField()
    current_votes = models.IntegerField(default=0)
    rank = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ('category', 'submission'),
        ]
