import datetime
import mock

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from ..models import SiteMode
from .factories import SubmissionFactory, UserFactory, VoterFactory


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


class ChangelogTest(TestCase):

    def setUp(self):
        self.url = reverse('changelog')
        self.merge_url = reverse('moderation_merge')
        self.remove_url = reverse('moderation_remove')

        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=self.password)

    def test_none(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_removals(self):
        good_submission = SubmissionFactory()
        bad_submission = SubmissionFactory()
        data = {
            'to_remove': bad_submission.id,
            'duplicate_of': '',
            'action': 'remove',
        }
        response = self.client.post(self.remove_url, data=data)

        response = self.client.get(self.url)
        self.assertContains(response, bad_submission.headline)
        self.assertNotContains(response, good_submission.headline)

    def test_merges(self):
        unmerged = SubmissionFactory()
        merge_parent = SubmissionFactory()
        merge_child = SubmissionFactory()

        response = self.client.post(self.merge_url, data={
            "action": "merge",
            "to_remove": merge_child.id,
            "duplicate_of": merge_parent.id,
        })

        response = self.client.get(self.url)
        self.assertContains(response, merge_child.headline)
        self.assertContains(
            response,
            'Merged into: <a href="{parenturl}">{parent}</a>'.format(
                parent=merge_parent.headline,
                parenturl=merge_parent.get_absolute_url()
            )
        )
        self.assertNotContains(response, unmerged.headline)
