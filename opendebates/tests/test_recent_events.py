from httplib import OK

from django.test import TestCase

import mock

from opendebates.models import RECENT_EVENTS_CACHE_ENTRY
from opendebates.tasks import update_recent_events
from opendebates.tests.factories import VoteFactory


class RecentEventsTest(TestCase):
    def setUp(self):
        self.vote = VoteFactory()

    def test_computing_recent_events(self):
        mock_cache = mock.MagicMock()
        with mock.patch('opendebates.tasks.cache', new=mock_cache):
            update_recent_events()
        mock_cache.set.assert_called_with(
            RECENT_EVENTS_CACHE_ENTRY,
            [self.vote, self.vote.submission],
            30
        )

    def test_view_returns_events(self):
        mock_cache = mock.MagicMock()
        vote2 = VoteFactory()
        mock_cache.get.return_value = [
            vote2,
            vote2.submission,
            self.vote,
            self.vote.submission
        ]
        with mock.patch('opendebates.views.cache', new=mock_cache):
            rsp = self.client.get('/recent/')
        mock_cache.get.assert_called_with(RECENT_EVENTS_CACHE_ENTRY, default=[])
        self.assertEqual(OK, rsp.status_code)
        html = rsp.content.decode('UTF-8')
        self.assertIn(vote2.submission.idea, html)
        self.assertIn(self.vote.submission.idea, html)
