from datetime import timedelta
from django.test import TestCase
from django.utils.timezone import now
from freezegun import freeze_time

from opendebates.models import SiteMode
from opendebates import utils


class EffectiveAfterTest(TestCase):
    def setUp(self):
        self.mode, _ = SiteMode.objects.get_or_create()
        self.start_time = now()
        SiteMode(announcement_headline='Tune in tonight!',
                 effective_after=self.start_time + timedelta(minutes=30)).save()
        SiteMode(announcement_headline='Watch - happening now!',
                 allow_voting_and_submitting_questions=False,
                 effective_after=self.start_time + timedelta(minutes=60)).save()
        SiteMode(announcement_headline='Thanks for participating!',
                 allow_voting_and_submitting_questions=False,
                 show_total_votes=False,
                 effective_after=self.start_time + timedelta(minutes=90)).save()

    def test_default_active_sitemode(self):
        self.assertEqual(utils.get_site_mode(), self.mode)

    def test_no_sitemode_effective_yet_creates_one(self):
        self.mode.delete()
        with freeze_time(self.start_time):
            self.assertEqual(SiteMode.objects.all().count(), 3)
            self.assertEqual(utils.get_site_mode().announcement_headline, None)
            self.assertEqual(SiteMode.objects.all().count(), 4)

    def test_effective_after(self):
        with freeze_time(self.start_time + timedelta(minutes=31)):
            self.assertEqual(utils.get_site_mode().announcement_headline,
                             'Tune in tonight!')

    def test_active_sitemode_is_latest_past_effective_after(self):
        with freeze_time(self.start_time + timedelta(minutes=61)):
            self.assertEqual(utils.get_site_mode().announcement_headline,
                             'Watch - happening now!')

    def test_sitemode_progression_takes_effect_automatically(self):
        url = '/'
        with freeze_time(self.start_time + timedelta(minutes=1)):
            rsp = self.client.get(url)
            self.assertContains(rsp, 'Submit a Question')
            self.assertContains(rsp, '<span class="number">')

        with freeze_time(self.start_time + timedelta(minutes=61)):
            rsp = self.client.get(url)
            self.assertNotContains(rsp, 'Submit a Question')
            self.assertContains(rsp, '<span class="number">')

        with freeze_time(self.start_time + timedelta(minutes=91)):
            rsp = self.client.get(url)
            self.assertNotContains(rsp, 'Submit a Question')
            self.assertNotContains(rsp, '<span class="number">')


class AnnouncementTest(TestCase):

    def setUp(self):
        self.mode, _ = SiteMode.objects.get_or_create()
        self.url = '/'

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
        self.mode.announcement_page_regex = "/registration/"
        self.mode.save()

        rsp = self.client.get('/registration/register/')
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get('/')
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        self.mode.announcement_page_regex = "^(?!/registration/register/).*$"
        self.mode.save()

        rsp = self.client.get('/registration/register/')
        self.assertNotIn('<div class="site-announcement warning">', rsp.content)
        self.assertNotIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get('/registration/login/')
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)

        rsp = self.client.get('/')
        self.assertIn('<div class="site-announcement warning">', rsp.content)
        self.assertIn('<a href="%s">' % link, rsp.content)


class InlineCSSTest(TestCase):

    def setUp(self):
        self.mode, _ = SiteMode.objects.get_or_create()
        self.url = '/'

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

        rsp = self.client.get('/registration/login/')
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
