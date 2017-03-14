from httplib import OK

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

import mock

from ..models import RECENT_EVENTS_CACHE_ENTRY, NUMBER_OF_VOTES_CACHE_ENTRY, Vote
from ..tasks import update_recent_events
from .factories import VoteFactory, SiteFactory, SiteModeFactory


class RecentEventsTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.vote = VoteFactory()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_computing_recent_events(self):
        mock_cache = mock.MagicMock()
        with mock.patch('opendebates.tasks.cache', new=mock_cache):
            update_recent_events()
        mock_cache.set.assert_any_call(
            RECENT_EVENTS_CACHE_ENTRY,
            [self.vote, self.vote.submission],
            24*3600
        )
        num = Vote.objects.count()
        mock_cache.set.assert_any_call(NUMBER_OF_VOTES_CACHE_ENTRY, num, 24*3600)

    def test_view_returns_events(self):
        mock_cache = mock.MagicMock()
        vote2 = VoteFactory()
        mode = vote2.submission.category.site_mode
        mock_cache.get.return_value = [
            vote2,
            vote2.submission,
            self.vote,
            self.vote.submission
        ]
        with mock.patch('opendebates.views.cache', new=mock_cache):
            rsp = self.client.get(reverse('recent_activity', kwargs={'prefix': mode.prefix}))
        mock_cache.get.assert_called_with(RECENT_EVENTS_CACHE_ENTRY, default=[])
        self.assertEqual(OK, rsp.status_code)
        html = rsp.content.decode('UTF-8')
        self.assertIn(vote2.submission.idea, html)
        self.assertIn(self.vote.submission.idea, html)
