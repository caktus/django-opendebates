from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

import re
import urlparse

from ..models import SiteMode
from .factories import SubmissionFactory, SiteFactory, SiteModeFactory
from .utilities import patch_cache_templatetag


@override_settings(SUBMISSIONS_PER_PAGE=1)
class PaginationTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        for i in range(2):
            SubmissionFactory()

        self.url = reverse('list_ideas', kwargs={'prefix': self.mode.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def find_first_page_link(self, content):
        link = re.search('<a\W+href="(.*)"\W+rel="page"\W+class="endless_page_link">2</a>',
                         content)
        self.assertNotEqual(None, link)
        return link.groups()[0]

    def test_pagination_appears(self):
        rsp = self.client.get(self.url)
        self.assertIn('endless_page_link', rsp.content)
        link = self.find_first_page_link(rsp.content)
        self.assertEqual('/{}/?page=2'.format(self.mode.prefix), link)

    def test_pagination_preserves_querystring(self):
        rsp = self.client.get(self.url + '?source=foo&utm_medium=email')
        self.assertIn('endless_page_link', rsp.content)
        link = self.find_first_page_link(rsp.content)
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['foo'], qs.get('source'))
        self.assertEqual(['email'], qs.get('utm_medium'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(3, len(qs.keys()))

    def test_pagination_drops_page_from_querystring(self):
        rsp = self.client.get(self.url + '?page=1&source=foo&utm_medium=email')
        self.assertIn('endless_page_link', rsp.content)
        link = self.find_first_page_link(rsp.content)
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['foo'], qs.get('source'))
        self.assertEqual(['email'], qs.get('utm_medium'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(3, len(qs.keys()))

    @patch_cache_templatetag()
    def test_pagination_cache_does_not_share_source(self):
        rsp = self.client.get(self.url + '?source=foo&utm_medium=email')
        link = self.find_first_page_link(rsp.content)
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['foo'], qs.get('source'))
        self.assertEqual(['email'], qs.get('utm_medium'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(3, len(qs.keys()))

        # As long as a different ?source is used, the cache lookup for the pagination fragment
        # should miss
        rsp = self.client.get(self.url + '?source=bar&utm_medium=social')
        link = self.find_first_page_link(rsp.content)
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['bar'], qs.get('source'))
        self.assertEqual(['social'], qs.get('utm_medium'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(3, len(qs.keys()))

    @patch_cache_templatetag()
    def test_pagination_cache_shares_rest_of_query_string(self):
        rsp = self.client.get(self.url + '?source=foo&utm_medium=email&bar=fleem&baz=foo')
        link = self.find_first_page_link(rsp.content)
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['foo'], qs.get('source'))
        self.assertEqual(['email'], qs.get('utm_medium'))
        self.assertEqual(['fleem'], qs.get('bar'))
        self.assertEqual(['foo'], qs.get('baz'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(5, len(qs.keys()))

        # As long as the same ?source is used, the cache lookup for the pagination fragment
        # should hit, even if that means serving links with someone else's query string
        # parameters
        rsp = self.client.get(self.url + '?source=foo&utm_medium=social&bar=morx')
        qs = urlparse.parse_qs(urlparse.urlparse(link).query)
        self.assertEqual(['foo'], qs.get('source'))
        self.assertEqual(['email'], qs.get('utm_medium'))
        self.assertEqual(['fleem'], qs.get('bar'))
        self.assertEqual(['foo'], qs.get('baz'))
        self.assertEqual(['2'], qs.get('page'))
        self.assertEqual(5, len(qs.keys()))
