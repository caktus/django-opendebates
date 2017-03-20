import datetime

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from .factories import (SubmissionFactory, UserFactory, VoterFactory,
                        SiteModeFactory, SiteFactory)


class ListIdeasTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)
        self.url = reverse('list_ideas', kwargs={'prefix': self.mode.prefix})

        for i in range(10):
            SubmissionFactory()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_list_ideas_uses_site_mode_from_context(self):
        """
        The category.site_mode in the Submission model shouldn't be accessed
        at all during list_ideas if we've successfully provided the SITE_MODE
        in the template context to the model.
        """
        with self.assertNumQueries(5):
            self.client.get(self.url)

    def test_most_since_last_debate_not_visible_if_no_previous_debate(self):
        mode = SiteModeFactory(previous_debate_time=None)

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': mode.prefix}))
        self.assertNotContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate(self):
        mode = SiteModeFactory(previous_debate_time=timezone.now() - datetime.timedelta(days=7))

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': mode.prefix}))
        self.assertContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate_in_future(self):
        mode = SiteModeFactory(previous_debate_time=timezone.now() + datetime.timedelta(days=7))

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': mode.prefix}))
        self.assertNotContains(response, "Most Votes Since Last Debate")


class ChangelogTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.url = reverse('changelog', kwargs={'prefix': self.mode.prefix})
        self.merge_url = reverse('moderation_merge', kwargs={'prefix': self.mode.prefix})
        self.remove_url = reverse('moderation_remove', kwargs={'prefix': self.mode.prefix})

        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=self.password)

    def tearDown(self):
        Site.objects.clear_cache()

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

    def test_duplicates(self):
        unmerged = SubmissionFactory()
        merge_parent = SubmissionFactory()
        merge_child = SubmissionFactory()

        response = self.client.post(self.merge_url, data={
            "action": "unmoderate",
            "to_remove": merge_child.id,
            "duplicate_of": merge_parent.id,
        })

        response = self.client.get(self.url)
        self.assertContains(response, merge_child.headline)
        self.assertContains(
            response,
            'Duplicate of: <a href="{parenturl}">{parent}</a>'.format(
                parent=merge_parent.headline,
                parenturl=merge_parent.get_absolute_url()
            )
        )
        self.assertNotContains(response, unmerged.headline)
