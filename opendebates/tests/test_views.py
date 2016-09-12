import mock

from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.models import SiteMode

from .factories import SubmissionFactory


class ListIdeasTest(TestCase):

    def setUp(self):
        self.url = reverse('list_ideas')

        for i in range(10):
            SubmissionFactory()

    @mock.patch('opendebates.utils.get_site_mode')
    def test_list_ideas_calls_get_site_mode_only_once(self, gsm_mock):
        gsm_mock.return_value = SiteMode.objects.get_or_create()[0]
        self.client.get(self.url)
        self.assertEqual(gsm_mock.call_count, 1)
