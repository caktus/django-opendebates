from functools import partial

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.html import escape

from opendebates.tests.factories import SubmissionFactory, SiteFactory, DebateFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# DebateMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class FacebookTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_facebook_site(self):
        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.debate.prefix}))
        self.assertContains(
            rsp,
            '<meta property="og:url" content="http://%s/%s"/>' % (
                self.debate.site.domain, self.debate.prefix)
        )
        self.assertContains(
            rsp,
            '<meta property="og:type" content="%s"/>' % 'website'
        )
        self.assertContains(
            rsp,
            '<meta property="og:title" content="%s"/>'
            % escape(self.debate.facebook_site_title)
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(self.debate.facebook_site_description)
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % self.debate.facebook_image
        )

    def test_facebook_question(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        rsp = self.client.get(question.get_absolute_url())
        self.assertContains(
            rsp,
            '<meta property="og:url" content="%s"/>' % question.really_absolute_url()
        )
        self.assertContains(
            rsp,
            '<meta property="og:type" content="%s"/>' % 'website'
        )
        self.assertContains(
            rsp,
            '<meta property="og:title" content="%s"/>'
            % escape(self.debate.facebook_question_title)
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(self.debate.facebook_question_description
                     .format(idea=question.idea))
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % self.debate.facebook_image
        )

    def test_facebook_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.debate.facebook_question_title.format(idea=question.idea),
            question.facebook_title()
        )

    def test_facebook_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.debate.facebook_question_description.format(idea=question.idea),
            question.facebook_description()
        )


class TwitterTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_twitter_site_card(self):
        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.debate.prefix}))
        self.assertContains(rsp, '<meta name="twitter:card" content="summary_large_image">')
        self.assertContains(rsp,
                            '<meta name="twitter:title" content="%s">'
                            % escape(self.debate.twitter_site_title))
        self.assertContains(rsp,
                            '<meta name="twitter:description" content="%s">'
                            % escape(self.debate.twitter_site_description))
        self.assertContains(
            rsp,
            '<meta name="twitter:image" content="%s">' % self.debate.twitter_image
        )

    def test_twitter_question_card(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        rsp = self.client.get(question.get_absolute_url())
        self.assertContains(rsp, '<meta name="twitter:card" content="summary_large_image">')
        self.assertContains(rsp,
                            '<meta name="twitter:title" content="%s">'
                            % escape(question.twitter_title()))
        self.assertContains(rsp,
                            '<meta name="twitter:description" content="%s">'
                            % escape(question.twitter_description()))
        self.assertContains(
            rsp,
            '<meta name="twitter:image" content="%s">' % self.debate.twitter_image
        )

    def test_twitter_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.debate.twitter_question_title.format(idea=question.idea),
            question.twitter_title()
        )

    def test_twitter_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.debate.twitter_question_description.format(idea=question.idea),
            question.twitter_description()
        )
