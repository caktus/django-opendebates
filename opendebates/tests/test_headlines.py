from httplib import OK

from django.core.urlresolvers import reverse
from django.test import TestCase

import mock

from opendebates.models import Submission
from opendebates.tests.factories import SubmissionFactory, UserFactory, VoterFactory

class RecentEventsTest(TestCase):
    def setUp(self):
        self.submission = SubmissionFactory()
        
    def test_headline_in_recent_events(self):
        mock_cache = mock.MagicMock()
        mock_cache.get.return_value = [
            self.submission
        ]
        with mock.patch('opendebates.views.cache', new=mock_cache):
            rsp = self.client.get('/recent/')

        html = rsp.content.decode('UTF-8')
        self.assertIn(self.submission.headline, html)

    def test_headline_contributes_to_search(self):
        rsp = self.client.get(reverse('search_ideas') + '?q=%s' % self.submission.headline)
        html = rsp.content.decode('UTF-8')
        self.assertIn(self.submission.get_absolute_url(), html)

    def test_headline_contributes_to_merge(self):
        submission2 = SubmissionFactory()

        user = UserFactory(password='secretpassword',
                           is_staff=True, is_superuser=True)
        voter = VoterFactory(user=user, email=user.email)
        assert self.client.login(username=user.username,
                                 password='secretpassword')
        
        merge_url = reverse('moderation_merge')        
        rsp = self.client.post(merge_url, data={
            "action": "merge",
            "to_remove": self.submission.id,
            "duplicate_of": submission2.id,
        })
        
        merged = Submission.objects.get(id=self.submission.id)
        remaining = Submission.objects.get(id=submission2.id)

        self.assertIn(self.submission.headline, remaining.keywords)
        
