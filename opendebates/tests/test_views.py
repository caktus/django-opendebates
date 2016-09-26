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

    def test_top_30_not_visible_if_no_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = None
        mode.save()

        response = self.client.get(self.url)
        self.assertNotContains(response, "Top 30 Since Last Debate")

    def test_top_30_visible_if_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = timezone.make_aware(
            datetime.datetime(2016, 1, 1, 12)
        )
        mode.save()

        response = self.client.get(self.url)
        self.assertContains(response, "Top 30 Since Last Debate")
