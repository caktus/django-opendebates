from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils.html import escape

from opendebates.tests.factories import SubmissionFactory, SiteFactory, SiteModeFactory


class FacebookTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_facebook_site(self):
        rsp = self.client.get('/')
        self.assertContains(
            rsp,
            '<meta property="og:url" content="http://%s"/>' % self.mode.site.domain
        )
        self.assertContains(
            rsp,
            '<meta property="og:type" content="%s"/>' % 'website'
        )
        self.assertContains(
            rsp,
            '<meta property="og:title" content="%s"/>'
            % escape(self.mode.facebook_site_title)
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(self.mode.facebook_site_description)
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % self.mode.facebook_image
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
            % escape(self.mode.facebook_question_title)
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(self.mode.facebook_question_description
                     .format(idea=question.idea))
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % self.mode.facebook_image
        )

    def test_facebook_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.mode.facebook_question_title.format(idea=question.idea),
            question.facebook_title()
        )

    def test_facebook_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.mode.facebook_question_description.format(idea=question.idea),
            question.facebook_description()
        )


class TwitterTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_twitter_site_card(self):
        rsp = self.client.get('/')
        self.assertContains(rsp, '<meta name="twitter:card" content="summary_large_image">')
        self.assertContains(rsp,
                            '<meta name="twitter:title" content="%s">'
                            % escape(self.mode.twitter_site_title))
        self.assertContains(rsp,
                            '<meta name="twitter:description" content="%s">'
                            % escape(self.mode.twitter_site_description))
        self.assertContains(
            rsp,
            '<meta name="twitter:image" content="%s">' % self.mode.twitter_image
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
            '<meta name="twitter:image" content="%s">' % self.mode.twitter_image
        )

    def test_twitter_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.mode.twitter_question_title.format(idea=question.idea),
            question.twitter_title()
        )

    def test_twitter_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            self.mode.twitter_question_description.format(idea=question.idea),
            question.twitter_description()
        )
