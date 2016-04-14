from django.conf import settings
from django.test import TestCase
from django.utils.html import escape

from opendebates.tests.factories import SubmissionFactory


class FacebookTest(TestCase):
    def test_facebook_site(self):
        rsp = self.client.get('/')
        self.assertContains(
            rsp,
            '<meta property="og:url" content="%s"/>' % settings.SITE_DOMAIN_WITH_PROTOCOL
        )
        self.assertContains(
            rsp,
            '<meta property="og:type" content="%s"/>' % 'website'
        )
        self.assertContains(
            rsp,
            '<meta property="og:title" content="%s"/>'
            % escape(settings.SITE_THEME['FACEBOOK_SITE_TITLE'])
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(settings.SITE_THEME['FACEBOOK_SITE_DESCRIPTION'])
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % settings.SITE_THEME['FACEBOOK_IMAGE']
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
            % escape(settings.SITE_THEME['FACEBOOK_QUESTION_TITLE'])
        )
        self.assertContains(
            rsp,
            '<meta property="og:description" content="%s"/>'
            % escape(settings.SITE_THEME['FACEBOOK_QUESTION_DESCRIPTION']
                     .format(idea=question.idea))
        )
        self.assertContains(
            rsp,
            '<meta property="og:image" content="%s"/>' % settings.SITE_THEME['FACEBOOK_IMAGE']
        )

    def test_facebook_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            settings.SITE_THEME['FACEBOOK_QUESTION_TITLE'].format(idea=question.idea),
            question.facebook_title()
        )

    def test_facebook_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            settings.SITE_THEME['FACEBOOK_QUESTION_DESCRIPTION'].format(idea=question.idea),
            question.facebook_description()
        )


class TwitterTest(TestCase):
    def test_twitter_site_card(self):
        rsp = self.client.get('/')
        self.assertContains(rsp, '<meta name="twitter:card" content="summary_large_image">')
        self.assertContains(rsp,
                            '<meta name="twitter:title" content="%s">'
                            % escape(settings.SITE_THEME['TWITTER_SITE_TITLE']))
        self.assertContains(rsp,
                            '<meta name="twitter:description" content="%s">'
                            % escape(settings.SITE_THEME['TWITTER_SITE_DESCRIPTION']))
        self.assertContains(
            rsp,
            '<meta name="twitter:image" content="%s">' % settings.SITE_THEME['TWITTER_IMAGE']
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
            '<meta name="twitter:image" content="%s">' % settings.SITE_THEME['TWITTER_IMAGE']
        )

    def test_twitter_title(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            settings.SITE_THEME['TWITTER_QUESTION_TITLE'].format(idea=question.idea),
            question.twitter_title()
        )

    def test_twitter_description(self):
        question = SubmissionFactory(idea="Bogus & Broken")
        self.assertEqual(
            settings.SITE_THEME['TWITTER_QUESTION_DESCRIPTION'].format(idea=question.idea),
            question.twitter_description()
        )
