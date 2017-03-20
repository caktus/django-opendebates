from django.contrib.sites.models import Site
from django.test import TestCase

from opendebates.models import Submission
from opendebates.tasks import update_trending_scores
from opendebates.tests.factories import SubmissionFactory, VoteFactory, SiteFactory


class TestScores(TestCase):
    def setUp(self):
        self.site = SiteFactory()

    def tearDown(self):
        Site.objects.clear_cache()

    def test_update_trending_scores(self):
        sub1 = SubmissionFactory()
        for i in range(30):
            VoteFactory(submission=sub1)
        self.assertEqual(0, sub1.random_id)
        self.assertEqual(0.0, sub1.score)
        update_trending_scores()
        sub1 = Submission.objects.get(pk=sub1.pk)
        self.assertNotEqual(0, sub1.random_id)
        self.assertGreater(sub1.score, 0.0)
