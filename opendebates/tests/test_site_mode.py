from functools import partial

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.tests.factories import SiteFactory, SiteModeFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# SiteModeMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class AnnouncementTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.url = reverse('list_ideas', kwargs={'prefix': self.mode.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_default_no_announcement(self):
        rsp = self.client.get(self.url)
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)

    def test_announcement_headline(self):
        headline = "Announcement: tune in tonight!"
        self.mode.announcement_headline = headline
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn(headline, rsp.content)

    def test_announcement_body(self):
        headline = "Announcement: tune in tonight!"
        body = "Don't forget to watch."
        self.mode.announcement_headline = headline
        self.mode.announcement_body = body
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn(body, rsp.content)

    def test_no_announcement_if_no_headline(self):
        body = "Announcement: tune in tonight!"
        self.mode.announcement_headline = None
        self.mode.announcement_body = body
        self.mode.announcement_link = "http://example.com"
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn(body, rsp.content)

    def test_announcement_link(self):
        headline = "Announcement: tune in tonight!"
        link = "http://example.com/the-special-page"
        self.mode.announcement_headline = headline
        self.mode.announcement_link = link
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

    def test_announcement_page_regex(self):
        headline = "Announcement: tune in tonight!"
        link = "http://example.com/the-special-page"
        self.mode.announcement_headline = headline
        self.mode.announcement_link = link
        self.mode.announcement_page_regex = "/{}/registration/".format(self.mode.prefix)
        self.mode.save()

        rsp = self.client.get(reverse('registration_register', kwargs={'prefix': self.mode.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.mode.prefix}))
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        self.mode.announcement_page_regex = "^(?!/{}/registration/register/).*$".format(
            self.mode.prefix)
        self.mode.save()

        rsp = self.client.get(reverse('registration_register', kwargs={'prefix': self.mode.prefix}))
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('auth_login', kwargs={'prefix': self.mode.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.mode.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)


class InlineCSSTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.url = reverse('list_ideas', kwargs={'prefix': self.mode.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_default_no_inline_css(self):
        rsp = self.client.get(self.url)
        self.assertNotIn(u'<style type="text/css" id="site-mode-inline-css">',
                         rsp.content)

    def test_inline_css(self):
        css = u"header { background: green !important; }"
        self.mode.inline_css = css
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertIn(u'<style type="text/css" id="site-mode-inline-css">',
                      rsp.content)
        self.assertIn(css, rsp.content)

        rsp = self.client.get(reverse('auth_login', kwargs={'prefix': self.mode.prefix}))
        self.assertIn(css, rsp.content)

    def test_admins_can_be_pretty_malicious_with_inline_css(self):
        """
        @@TODO maybe content should be validated as legitimate CSS;
        at the moment there's no validation or html-escaping anywhere.
        """
        css = u"</style></head><body></body></html>"
        self.mode.inline_css = css
        self.mode.save()

        rsp = self.client.get(self.url)
        self.assertIn(u'<style type="text/css" id="site-mode-inline-css">',
                      rsp.content)
        self.assertIn(css, rsp.content)
