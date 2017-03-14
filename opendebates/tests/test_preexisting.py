from django.contrib.sites.models import Site
from django.test import TestCase, Client
from django.test.utils import override_settings

from ..models import Category
from .factories import CategoryFactory, SiteFactory, SiteModeFactory


@override_settings(STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False)
class ViewTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        CategoryFactory(name="category one")

    def tearDown(self):
        Site.objects.clear_cache()

    def test_data(self):
        self.assertEqual(Category.objects.filter(name="category one").count(), 1)

    def test_healthcheck_view(self):
        c = Client()
        response = c.get('/healthcheck.html')
        self.assertEqual(response.status_code, 200)
