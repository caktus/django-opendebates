from django.test import TestCase, Client
from django.test.utils import override_settings
from .models import Category


@override_settings(STATICFILES_STORAGE='pipeline.storage.NonPackagingPipelineStorage',
                   PIPELINE_ENABLED=False)
class ViewTest(TestCase):

    def setUp(self):
        Category.objects.create(name="category one")

    def test_data(self):
        self.assertEqual(Category.objects.filter(name="category one").count(), 1)

    def test_test_view(self):
        c = Client()
        response = c.get('/test/')
        self.assertEqual(response.status_code, 200)
