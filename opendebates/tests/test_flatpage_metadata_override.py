from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import TestCase
from django.utils.html import escape

from opendebates.models import FlatPageMetadataOverride
from opendebates import site_defaults
from .factories import SiteFactory, SiteModeFactory


class FlatPageTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.page1_content = 'About the site'
        self.page1 = FlatPage(url='/about/', title='About',
                              content=self.page1_content)
        self.page1.save()
        self.page1.sites.add(self.site)
        self.page2_content = '[An embedded video]'
        self.page2 = FlatPage(url='/watch/', title='Watch Now!',
                              content=self.page2_content)
        self.page2.save()
        self.page2.sites.add(self.site)

        FlatPageMetadataOverride(page=self.page2).save()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_metadata_not_overridden(self):
        rsp = self.client.get(self.page1.url)
        self.assertContains(rsp, self.page1_content)
        self.assertContains(rsp, escape(site_defaults.FACEBOOK_SITE_TITLE))
        self.assertContains(rsp, escape(site_defaults.FACEBOOK_SITE_DESCRIPTION))
        self.assertContains(rsp, escape(site_defaults.FACEBOOK_IMAGE))

    def test_default_metadata_overrides(self):
        rsp = self.client.get(self.page2.url)
        self.assertContains(rsp, self.page2_content)
        self.assertNotContains(rsp, escape(site_defaults.FACEBOOK_SITE_TITLE))
        self.assertNotContains(rsp, escape(site_defaults.FACEBOOK_SITE_DESCRIPTION))
        self.assertNotContains(rsp, escape(site_defaults.FACEBOOK_IMAGE))
        self.assertNotContains(rsp, escape(site_defaults.TWITTER_IMAGE))
        self.assertContains(rsp, escape(site_defaults.FLATPAGE_FACEBOOK_TITLE))
        self.assertContains(rsp, escape(site_defaults.FLATPAGE_FACEBOOK_DESCRIPTION))
        self.assertContains(rsp, escape(site_defaults.FLATPAGE_FACEBOOK_IMAGE))
        self.assertContains(rsp, escape(site_defaults.FLATPAGE_TWITTER_IMAGE))

    def test_custom_metadata_overrides(self):
        FlatPageMetadataOverride(
            page=self.page1,
            facebook_title='Foo! Foo! Foo!',
            twitter_description='lorem ipsum dolor sit amet').save()
        rsp = self.client.get(self.page1.url)
        self.assertContains(rsp, escape('Foo! Foo! Foo!'))
        self.assertContains(rsp, escape('lorem ipsum dolor sit amet'))
        self.assertContains(rsp, escape(site_defaults.FLATPAGE_TWITTER_IMAGE))
