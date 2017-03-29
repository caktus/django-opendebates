from functools import partial

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

import mock

from ..models import Submission
from .factories import SubmissionFactory, UserFactory, VoterFactory, SiteFactory, SiteModeFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# SiteModeMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class HeadlineTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.submission = SubmissionFactory()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_headline_in_recent_events(self):
        mock_cache = mock.MagicMock()
        mock_cache.get.return_value = [
            self.submission
        ]
        with mock.patch('opendebates.views.cache', new=mock_cache):
            rsp = self.client.get(reverse('recent_activity', kwargs={'prefix': self.mode.prefix}))

        html = rsp.content.decode('UTF-8')
        self.assertIn(self.submission.headline, html)

    def test_headline_contributes_to_search(self):
        rsp = self.client.get(
            reverse('search_ideas', kwargs={'prefix': self.mode.prefix}) +
            '?q=%s' % self.submission.headline)
        html = rsp.content.decode('UTF-8')
        self.assertIn(self.submission.get_absolute_url(), html)

    def test_headline_contributes_to_merge(self):
        submission2 = SubmissionFactory()

        user = UserFactory(password='secretpassword',
                           is_staff=True, is_superuser=True)
        VoterFactory(user=user, email=user.email)
        assert self.client.login(username=user.username,
                                 password='secretpassword')

        merge_url = reverse('moderation_merge', kwargs={'prefix': self.mode.prefix})
        self.client.post(merge_url, data={
            "action": "merge",
            "to_remove": self.submission.id,
            "duplicate_of": submission2.id,
        })

        remaining = Submission.objects.get(id=submission2.id)

        self.assertIn(self.submission.headline, remaining.keywords)
