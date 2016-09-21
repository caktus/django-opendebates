from django.core.urlresolvers import reverse
from django.test import TestCase

from .factories import SubmissionFactory


class ListIdeasTest(TestCase):

    def setUp(self):
        self.url = reverse('list_ideas')

        for i in range(10):
            SubmissionFactory()

    def test_list_ideas_uses_site_mode_from_context(self):
        """
        The category.site_mode in the Submission model shouldn't be accessed
        at all during list_ideas if we've successfully provided the SITE_MODE
        in the template context to the model.
        """
        with self.assertNumQueries(4):
            self.client.get(self.url)
