from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

import re

from .factories import SubmissionFactory, SiteFactory, SiteModeFactory


@override_settings(SUBMISSIONS_PER_PAGE=2)
class NavigationTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)
        self.url = reverse('list_ideas', kwargs={'prefix': self.mode.prefix})
        self.search_url = reverse('search_ideas', kwargs={'prefix': self.mode.prefix})

        SubmissionFactory(votes=1)
        SubmissionFactory(votes=2)
        SubmissionFactory(headline="Something about ducks", votes=10)
        SubmissionFactory(headline="Another thing about ducks", votes=5)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_sort_by_option_is_sticky(self):
        rsp = self.client.get(self.url + '?sort=%2Bvotes')
        # Make sure it's actually sorting properly
        self.assertNotContains(rsp, 'ducks')
        self.assertNotContains(rsp, '<option value="-votes" selected>')
        self.assertContains(rsp, '<option value="+votes" selected>')

        rsp = self.client.get(self.url + '?sort=-votes')
        # Make sure it's actually sorting properly
        self.assertContains(rsp, 'ducks')
        self.assertContains(rsp, '<option value="-votes" selected>')

    def test_search_term_is_sticky(self):
        rsp = self.client.get(self.search_url + "?q=something+ducks")
        # Make sure it's actually searching properly
        self.assertContains(rsp, 'ducks')
        self.assertContains(rsp, '<input name="q" value="something ducks"')

    def test_search_term_inserts_into_sort_form(self):
        rsp = self.client.get(self.search_url + "?q=something+ducks")
        form_html = ('\<form action="{search}" method="GET" '
                     'class="form-inline"\>\W+'
                     '\<input type="hidden" name="q" '
                     'value="something ducks"\>'.format(
                         search=self.search_url))
        self.assertNotEqual(None, re.search(form_html, rsp.content))
