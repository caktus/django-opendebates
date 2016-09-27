import datetime
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from ..models import SiteMode
from .factories import SubmissionFactory


class ListIdeasTest(TestCase):

    def setUp(self):
        self.url = reverse('list_ideas')

        for i in range(10):
            SubmissionFactory()

    @mock.patch('opendebates.models.Submission._get_site_mode')
    def test_list_ideas_uses_site_mode_from_context(self, gsm_mock):
        """
        The _get_site_mode method in the Submission model shouldn't be called
        at all during list_ideas if we've successfully provided the SITE_MODE
        in the template context to the model.
        """
        self.client.get(self.url)
        self.assertEqual(gsm_mock.call_count, 0)

    def test_most_since_last_debate_not_visible_if_no_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = None
        mode.save()

        response = self.client.get(self.url)
        self.assertNotContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = timezone.now() - datetime.timedelta(days=7)
        mode.save()

        response = self.client.get(self.url)
        self.assertContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate_in_future(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = timezone.now() + datetime.timedelta(days=7)
        mode.save()

        response = self.client.get(self.url)
        self.assertNotContains(response, "Most Votes Since Last Debate")
