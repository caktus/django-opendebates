from functools import partial

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.tests.factories import SiteFactory, DebateFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# DebateMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class AnnouncementTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_default_no_announcement(self):
        rsp = self.client.get(self.url)
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)

    def test_announcement_headline(self):
        headline = "Announcement: tune in tonight!"
        self.debate.announcement_headline = headline
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn(headline, rsp.content)

    def test_announcement_body(self):
        headline = "Announcement: tune in tonight!"
        body = "Don't forget to watch."
        self.debate.announcement_headline = headline
        self.debate.announcement_body = body
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn(body, rsp.content)

    def test_no_announcement_if_no_headline(self):
        body = "Announcement: tune in tonight!"
        self.debate.announcement_headline = None
        self.debate.announcement_body = body
        self.debate.announcement_link = "http://example.com"
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn(body, rsp.content)

    def test_announcement_link(self):
        headline = "Announcement: tune in tonight!"
        link = "http://example.com/the-special-page"
        self.debate.announcement_headline = headline
        self.debate.announcement_link = link
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

    def test_announcement_page_regex(self):
        headline = "Announcement: tune in tonight!"
        link = "http://example.com/the-special-page"
        self.debate.announcement_headline = headline
        self.debate.announcement_link = link
        self.debate.announcement_page_regex = "/{}/registration/".format(self.debate.prefix)
        self.debate.save()

        rsp = self.client.get(reverse('registration_register', kwargs={'prefix': self.debate.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.debate.prefix}))
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        self.debate.announcement_page_regex = "^(?!/{}/registration/register/).*$".format(
            self.debate.prefix)
        self.debate.save()

        rsp = self.client.get(reverse('registration_register', kwargs={'prefix': self.debate.prefix}))
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('auth_login', kwargs={'prefix': self.debate.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get(reverse('list_ideas', kwargs={'prefix': self.debate.prefix}))
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)


class InlineCSSTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_default_no_inline_css(self):
        rsp = self.client.get(self.url)
        self.assertNotIn(u'<style type="text/css" id="debate-inline-css">',
                         rsp.content)

    def test_inline_css(self):
        css = u"header { background: green !important; }"
        self.debate.inline_css = css
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertIn(u'<style type="text/css" id="debate-inline-css">',
                      rsp.content)
        self.assertIn(css, rsp.content)

        rsp = self.client.get(reverse('auth_login', kwargs={'prefix': self.debate.prefix}))
        self.assertIn(css, rsp.content)

    def test_admins_can_be_pretty_malicious_with_inline_css(self):
        """
        @@TODO maybe content should be validated as legitimate CSS;
        at the moment there's no validation or html-escaping anywhere.
        """
        css = u"</style></head><body></body></html>"
        self.debate.inline_css = css
        self.debate.save()

        rsp = self.client.get(self.url)
        self.assertIn(u'<style type="text/css" id="debate-inline-css">',
                      rsp.content)
        self.assertIn(css, rsp.content)
