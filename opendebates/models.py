# coding=utf-8
import datetime
from django.db import models
from django.conf import settings
from django.core.signing import Signer
from djorm_pgfulltext.models import SearchManager
from djorm_pgfulltext.fields import VectorField
from urllib import quote_plus
from django.utils.translation import ugettext_lazy as _
from caching.base import CachingManager, CachingMixin


NUMBER_OF_VOTES_CACHE_ENTRY = 'number_of_votes'
RECENT_EVENTS_CACHE_ENTRY = 'recent_events_cache_entry'


class Category(CachingMixin, models.Model):

    name = models.CharField(max_length=255)

    objects = CachingManager()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name_plural = _("categories")


class Submission(models.Model):

    def user_display_name(self):
        return self.voter.user_display_name()

    category = models.ForeignKey(Category)
    idea = models.TextField(verbose_name=_('Question'))

    headline = models.TextField(null=True, blank=True)
    followup = models.TextField(null=True, blank=True)

    citation = models.URLField(null=True, blank=True, db_index=True,
                               verbose_name=_("Optional link to full proposal or reference"))
    citation_verified = models.BooleanField(default=False, db_index=True)

    voter = models.ForeignKey("Voter")
    created_at = models.DateTimeField(db_index=True)

    ip_address = models.CharField(max_length=255, db_index=True)

    editors_pick = models.BooleanField(default=False)
    approved = models.BooleanField(default=False, db_index=True)

    # if True, will not show up again in moderation list.
    moderated_removal = models.BooleanField(default=False, db_index=True)

    has_duplicates = models.BooleanField(default=False, db_index=True)

    duplicate_of = models.ForeignKey('opendebates.Submission', null=True, blank=True,
                                     related_name="duplicates")

    votes = models.IntegerField(default=0, db_index=True)
    score = models.FloatField(default=0, db_index=True)
    rank = models.FloatField(default=0, db_index=True)

    random_id = models.FloatField(default=0, db_index=True)

    search_index = VectorField()

    keywords = models.TextField(null=True, blank=True)

    objects = SearchManager(fields=["idea", "keywords"],
                            auto_update_search_field=True)

    source = models.CharField(max_length=255, null=True, blank=True)

    def get_recent_votes(self):
        timespan = datetime.datetime.now() - datetime.timedelta(1)
        return Vote.objects.filter(submission=self, created_at__gte=timespan).count()

    def get_duplicates(self):
        if not self.has_duplicates:
            return None
        return Submission.objects.select_related(
            "voter", "category", "voter__user").filter(
            approved=True, duplicate_of=self)

    def __unicode__(self):
        return self.idea

    @models.permalink
    def get_absolute_url(self):
        return "vote", [self.id]

    def my_tweet_text(self):
        return _(u"Vote for my progressive idea for @ThinkBigUS #BigIdeasProject. "
                 "30 leaders in Congress will see top ideas!")

    def tweet_text(self):
        text = _(u"Let's make sure 30 leaders in Congress see this #BigIdea about "
                 "%(category_name)s - please vote and RT!" % {
                     "category_name": quote_plus(self.category.name)})
        if self.voter.twitter_handle:
            text += u" h/t @%s" % self.voter.twitter_handle
        return text

    def facebook_text(self):
        if len(self.idea) > 240:
            return self.idea[:240] + u'…'
        return self.idea

    def facebook_url(self):
        return u"https://www.facebook.com/sharer/sharer.php?&u=%(idea_url)s" % {
            "idea_url": quote_plus(self.really_absolute_url()),
            }

    def really_absolute_url(self):
        return settings.SITE_DOMAIN_WITH_PROTOCOL + self.get_absolute_url()

    def email_subject_text(self):
        return _("Vote+for+my+Big+Idea!")

    def email_body_text(self):
        return _("I+posted+an+idea+on+The+Big+Ideas+Project+--+30+members+of+Congress"
                 "+will+see+the+top+20+ideas!+Please+click+here+to+see+it+and+vote+on"
                 "+my+idea+--+and+share+it+with+your+friends!")

    def email_url(self):
        return u"mailto:?subject=%s&body=%s" % (
            self.email_subject_text(), self.email_body_text(), self.really_absolute_url())

    def twitter_url(self):
        url_tmpl = u"https://twitter.com/intent/tweet?url=" + \
                   "%(SITE_DOMAIN)s%(idea_url)s&text=%(tweet_text)s"
        return url_tmpl % {
            "SITE_DOMAIN": quote_plus(settings.SITE_DOMAIN_WITH_PROTOCOL),
            "idea_url": quote_plus(self.get_absolute_url()),
            "tweet_text": quote_plus(self.tweet_text()),
            }


class ZipCode(CachingMixin, models.Model):
    zip = models.CharField(max_length=10, unique=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)

    objects = CachingManager()


class Voter(models.Model):

    def user_display_name(self):
        voter = self
        if voter.display_name:
            return voter.display_name

        if not voter.user:
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

    ip_address = models.CharField(max_length=255, db_index=True)
    request_headers = models.TextField(null=True, blank=True)

    original_merged_submission = models.ForeignKey(Submission, null=True, blank=True,
                                                   related_name="votes_merged_elsewhere")

    class Meta:
        unique_together = [("submission", "voter")]

    created_at = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=255, null=True, blank=True)


class Candidate(models.Model):
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

    class Meta:
        unique_together = [
            ('to_remove', 'voter'),
        ]
