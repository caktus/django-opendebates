# coding=utf-8

from django.contrib.sites.models import Site
from django.test import TestCase
import urlparse

from .factories import UserFactory, VoterFactory, SubmissionFactory, SiteFactory, DebateFactory, VoteFactory, \
    CandidateFactory


class SubmissionReallyAbsoluteUrlTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.submission = SubmissionFactory()
        self.site.domain = 'example.net'
        self.site.save()
        self.submission_id = self.submission.id

    def tearDown(self):
        Site.objects.clear_cache()

    def test_default(self):
        self.assertEqual(
            'https://testserver/%s/questions/%s/vote/' % (
                self.debate.prefix, self.submission_id),
            self.submission.really_absolute_url())

    def test_source(self):
        url = self.submission.really_absolute_url("fb")

        # When a source is included, nothing before querystring is affected
        self.assertEqual(self.submission.really_absolute_url(),
                         url.split('?')[0])

        # The query string will include a ?source parameter prefixed with share-
        # that includes both the platform we are sharing on, and the question ID
        parsed = urlparse.urlparse(url)
        self.assertEqual(parsed.query, 'source=share-fb-%s' % self.submission_id)

        parsed = urlparse.urlparse(self.submission.really_absolute_url('foo'))
        self.assertEqual(parsed.query, 'source=share-foo-%s' % self.submission_id)


class SubmissionTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.submission = SubmissionFactory()
        self.site.domain = 'example.net'
        self.site.save()
        self.submission_id = self.submission.id

    def tearDown(self):
        Site.objects.clear_cache()

    def test_get_recent_votes(self):
        self.vote1 = VoteFactory(submission=self.submission)

        self.assertEqual(self.submission.get_recent_votes(), 1)

    def test_get_duplicates__empty(self):
        self.assertIsNone(self.submission.get_duplicates())

    def test_get_duplicates(self):
        duplicate = SubmissionFactory()
        duplicate.duplicate_of = self.submission
        duplicate.has_duplicates = True
        duplicate.save()

        self.submission.has_duplicates = True
        self.submission.duplicate_of = duplicate
        self.submission.save()

        self.assertEqual(self.submission.get_duplicates().count(), 1)
        self.assertEqual(duplicate.get_duplicates().count(), 1)

    def test_tweet_text(self):
        self.assertIsNotNone(self.submission.tweet_text())

        self.submission.voter.twitter_handle = '@testTwitterUser'
        self.submission.voter.save()
        self.assertIn(self.submission.voter.twitter_handle, self.submission.tweet_text())

    def test_facebook_text__short(self):
        self.submission.idea = 'Short Idea'
        self.submission.save()
        self.assertEqual(self.submission.facebook_text(), self.submission.idea)

    def test_facebook_text__long(self):
        short_desc = 'Very Long Idea'
        self.submission.idea = short_desc * 100
        self.submission.save()
        self.assertIn(short_desc, self.submission.facebook_text())
        self.assertIn(u'…', self.submission.facebook_text())

    def test_reddit_url(self):
        self.assertIsNotNone(self.submission.reddit_url())

    def test_sms_url(self):
        self.assertIsNotNone(self.submission.sms_url())


class VoterUserDisplayNameTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_anonymous(self):
        voter = VoterFactory(user=None)
        self.assertEqual('Somebody', str(voter.user_display_name()))

    def test_user_blank(self):
        user = UserFactory(first_name='', last_name='')
        voter = VoterFactory(user=user)
        self.assertEqual('Somebody', str(voter.user_display_name()))

    def test_user_no_last_name(self):
        user = UserFactory(first_name='George', last_name='')
        voter = VoterFactory(user=user)
        self.assertEqual('George', str(voter.user_display_name()))

    def test_user_both_names(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user)
        self.assertEqual('George W.', str(voter.user_display_name()))

    def test_user_with_state(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, state='VA')
        self.assertEqual('George W. from VA', str(voter.user_display_name()))

    def test_user_with_explicit_display_name(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, display_name='Prez1')
        self.assertEqual('Prez1', str(voter.user_display_name()))

    def test_voter_with_explicit_display_name_with_state(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, display_name='Prez1', state='VA')
        self.assertEqual('Prez1 from VA', str(voter.user_display_name()))


class VoterTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)
        self.user = UserFactory(first_name='test', last_name='user')
        self.voter = VoterFactory(user=self.user)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_account_token(self):
        self.assertIsNotNone((self.voter.account_token()))


class CandidateTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)
        self.candidate = CandidateFactory(
            debate=self.debate, first_name='test', last_name='candidate'
        )

    def tearDown(self):
        Site.objects.clear_cache()

    def test_save(self):
        self.candidate.save()
        self.assertIsNotNone(self.candidate.display_name)
        self.assertIsNotNone(unicode(self.candidate))
