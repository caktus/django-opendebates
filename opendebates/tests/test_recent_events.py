from functools import partial
from httplib import OK

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

import mock

from ..models import RECENT_EVENTS_CACHE_ENTRY, NUMBER_OF_VOTES_CACHE_ENTRY
from ..tasks import update_recent_events
from .factories import CategoryFactory, SubmissionFactory, VoteFactory, SiteFactory, SiteModeFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# SiteModeMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class RecentEventsTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode1 = SiteModeFactory(site=self.site)
        self.mode2 = SiteModeFactory(site=self.site)

        cat1 = CategoryFactory(site_mode=self.mode1)
        cat2 = CategoryFactory(site_mode=self.mode2)
        sub1 = SubmissionFactory(category=cat1)
        sub2 = SubmissionFactory(category=cat2)

        self.vote1 = VoteFactory(submission=sub1)
        self.vote2 = VoteFactory(submission=sub2)
        self.vote3 = VoteFactory(submission=sub2)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_computing_recent_events(self):
        mock_cache = mock.MagicMock()
        with mock.patch('opendebates.tasks.cache', new=mock_cache):
            update_recent_events()

        mock_cache.set.assert_any_call(
            RECENT_EVENTS_CACHE_ENTRY.format(self.mode1.id),
            [self.vote1, self.vote1.submission],
            24*3600
        )
        mock_cache.set.assert_any_call(
            RECENT_EVENTS_CACHE_ENTRY.format(self.mode2.id),
            [self.vote3, self.vote2, self.vote2.submission],
            24*3600
        )

        mock_cache.set.assert_any_call(
            NUMBER_OF_VOTES_CACHE_ENTRY.format(self.mode1.id),
            1,
            24*3600
        )
        mock_cache.set.assert_any_call(
            NUMBER_OF_VOTES_CACHE_ENTRY.format(self.mode2.id),
            2,
            24*3600
        )

    def test_view_returns_events(self):
        mock_cache = mock.MagicMock()

        mock_cache.get.return_value = [
            self.vote3,
            self.vote3.submission,
            self.vote2,
            self.vote2.submission
        ]
        with mock.patch('opendebates.views.cache', new=mock_cache):
            rsp = self.client.get(reverse('recent_activity',
                                          kwargs={'prefix': self.mode2.prefix}))
        mock_cache.get.assert_called_with(
            RECENT_EVENTS_CACHE_ENTRY.format(self.mode2.id), default=[])
        self.assertEqual(OK, rsp.status_code)
        html = rsp.content.decode('UTF-8')
        self.assertIn(self.vote3.submission.idea, html)
        self.assertIn(self.vote2.submission.idea, html)
        self.assertNotIn(self.vote1.submission.idea, html)
