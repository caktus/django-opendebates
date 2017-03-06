import datetime

from django.test import TestCase
from django.utils import timezone

from opendebates.models import Submission
from opendebates.tasks import update_trending_scores
from opendebates.tests.factories import SubmissionFactory, VoteFactory
from opendebates.utils import get_site_mode


class TestScores(TestCase):
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

    def test_update_trending_scores_old_debate(self):
        site_mode = get_site_mode()
        site_mode.debate_time = timezone.now() - datetime.timedelta(days=1)
        site_mode.save()
        sub1 = SubmissionFactory()
        for i in range(30):
            VoteFactory(submission=sub1)
        self.assertEqual(0, sub1.random_id)
        self.assertEqual(0.0, sub1.score)
        update_trending_scores()
        # no changes should have been made
        sub1 = Submission.objects.get(pk=sub1.pk)
        self.assertEqual(0, sub1.random_id)
        self.assertEqual(0.0, sub1.score)
