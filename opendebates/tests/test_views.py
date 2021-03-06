import datetime
from functools import partial

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from .factories import (SubmissionFactory, UserFactory, VoterFactory,
                        DebateFactory, SiteFactory, CategoryFactory)


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# DebateMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class RootRedirectTest(TestCase):

    def setUp(self):
        # 'testserver' is the default domain for SiteFactory, but it's included
        # here for clarity.
        self.site = SiteFactory(domain='testserver')
        self.other_site = SiteFactory(domain='otherdomain')
        # really old debate
        DebateFactory(
            site=self.site,
            debate_time=timezone.now() - datetime.timedelta(days=200),
        )
        # semi-recent debate
        self.previous_debate = DebateFactory(
            site=self.site,
            debate_time=timezone.now() - datetime.timedelta(days=20),
        )
        # upcoming debate
        self.next_debate = DebateFactory(
            site=self.site,
            debate_time=timezone.now() + datetime.timedelta(days=1),
        )

    def tearDown(self):
        Site.objects.clear_cache()

    def test_next_debate(self):
        DebateFactory(
            site=self.site,
            debate_time=timezone.now() + datetime.timedelta(days=20),
        )
        r = self.client.get('/')
        self.assertRedirects(r, '/%s/' % self.next_debate.prefix)

    def test_only_previous_debate(self):
        self.next_debate.delete()
        r = self.client.get('/')
        self.assertRedirects(r, '/%s/' % self.previous_debate.prefix)

    def test_site_with_no_debates(self):
        with self.settings(ALLOWED_HOSTS=[self.other_site.domain]):
            r = self.client.get('/', SERVER_NAME=self.other_site.domain)
        self.assertRedirects(r, 'https://opendebatecoalition.com', fetch_redirect_response=False)


class ListIdeasTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)
        self.url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})

        for i in range(10):
            SubmissionFactory()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_list_ideas_uses_debate_from_context(self):
        """
        The category.debate in the Submission model shouldn't be accessed
        at all during list_ideas if we've successfully provided the DEBATE
        in the template context to the model.
        """
        with self.assertNumQueries(4):
            self.client.get(self.url)

    def test_most_since_last_debate_not_visible_if_no_previous_debate(self):
        debate = DebateFactory(previous_debate_time=None)

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': debate.prefix}))
        self.assertNotContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate(self):
        debate = DebateFactory(previous_debate_time=timezone.now() - datetime.timedelta(days=7))

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': debate.prefix}))
        self.assertContains(response, "Most Votes Since Last Debate")

    def test_most_since_last_debate_visible_if_previous_debate_in_future(self):
        debate = DebateFactory(previous_debate_time=timezone.now() + datetime.timedelta(days=7))

        response = self.client.get(reverse('list_ideas', kwargs={'prefix': debate.prefix}))
        self.assertNotContains(response, "Most Votes Since Last Debate")


class ListCategoryTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)
        self.category = CategoryFactory(debate=self.debate)
        self.url = reverse('list_category', kwargs={'prefix': self.debate.prefix, 'cat_id': self.category.pk})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_list_category(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Choose a Category")
        self.assertEquals(response.status_code, 200)


class CategorySearchTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site, allow_sorting_by_votes=False)
        self.category = CategoryFactory(debate=self.debate)
        self.url = reverse('category_search', kwargs={'prefix': self.debate.prefix, 'cat_id': self.category.pk})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_category_search(self):
        response = self.client.get(self.url + "?q=election&citations_only=true&sort=votes")
        self.assertContains(response, "Choose a Category")
        self.assertEquals(response.status_code, 200)


class ChangelogTest(TestCase):

    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.url = reverse('changelog', kwargs={'prefix': self.debate.prefix})
        self.merge_url = reverse('moderation_merge', kwargs={'prefix': self.debate.prefix})
        self.remove_url = reverse('moderation_remove', kwargs={'prefix': self.debate.prefix})

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
