import urlparse

from django.test import TestCase, override_settings
from mock import patch, Mock

from opendebates.context_processors import global_vars
from opendebates.tests.factories import SubmissionFactory


class NumberOfVotesTest(TestCase):
    def test_number_of_votes(self):
        mock_request = Mock()
        with patch('opendebates.utils.cache') as mock_cache:
            mock_cache.get.return_value = 2
            context = global_vars(mock_request)
            self.assertEqual(2, int(context['NUMBER_OF_VOTES']))


class ThemeTests(TestCase):

    def setUp(self):
        self.idea = SubmissionFactory()

    @override_settings(SITE_THEME={'HASHTAG': 'TestHashtag'})
    def test_email_url(self):
        email_url = self.idea.email_url()
        fields = urlparse.parse_qs(urlparse.urlparse(email_url).query)
        self.assertTrue('subject' in fields, fields)
        self.assertTrue('#TestHashtag' in fields['subject'][0], fields['subject'][0])
