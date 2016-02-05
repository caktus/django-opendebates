from django.core.urlresolvers import reverse
from django.test import TestCase
import json

from opendebates.models import Submission, Vote
from .factories import UserFactory, VoterFactory, SubmissionFactory


class ModerationTest(TestCase):

    def setUp(self):
        self.first_submission = SubmissionFactory()
        self.second_submission = SubmissionFactory()
        self.third_submission = SubmissionFactory()
        self.url = reverse('moderation_mark_duplicate')
        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=self.password)

    def test_merge_submission(self):
        self.assertEqual(self.second_submission.has_duplicates, False)
        self.assertEqual(self.second_submission.duplicate_of, None)
        self.assertEqual(self.second_submission.keywords, None)
        self.assertEqual(self.third_submission.has_duplicates, False)
        self.assertEqual(self.third_submission.duplicate_of, None)
        self.assertEqual(self.third_submission.keywords, None)

        rsp = self.client.post(self.url, data={
            "confirm": "confirm",
            "handling": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.url)

        merged = Submission.objects.get(id=self.third_submission.id)
        remaining = Submission.objects.get(id=self.second_submission.id)

        # The merged submission should now be marked as a duplicate
        self.assertEqual(merged.duplicate_of, remaining)

        # The remaining submission should now be marked as having duplicates
        self.assertEqual(remaining.has_duplicates, True)

        # The merged submission's content is copied into the remaining one's keywords
        self.assertIn(merged.idea, remaining.keywords)

        # Viewing the merged submission now lands visitors on the remaining submission
        # with a fragment referring to the merged submission's place on the page
        rsp = self.client.get(merged.get_absolute_url())
        self.assertRedirects(rsp,
                             reverse('show_idea', args=[remaining.id]) + (
                                 "#i%s" % merged.id))

    def test_nested_merge_submission(self):
        self.client.post(self.url, data={
            "confirm": "confirm",
            "handling": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.client.post(self.url, data={
            "confirm": "confirm",
            "handling": "merge",
            "to_remove": self.second_submission.id,
            "duplicate_of": self.first_submission.id,
        })

        merged_deep = Submission.objects.get(id=self.third_submission.id)
        merged_shallow = Submission.objects.get(id=self.second_submission.id)
        remaining = Submission.objects.get(id=self.first_submission.id)

        self.assertEqual(merged_deep.duplicate_of, merged_shallow)
        self.assertEqual(merged_shallow.duplicate_of, remaining)
        self.assertEqual(merged_shallow.has_duplicates, True)
        self.assertEqual(remaining.has_duplicates, True)

        # After a nested merge, the remaining submission's keywords will include
        # text from all merged submissions up the chain
        self.assertIn(merged_shallow.idea, remaining.keywords)
        self.assertIn(merged_deep.idea, remaining.keywords)

    def test_merged_votes_relocate_if_unique(self):
        "During a merge, only unique votes get moved over to the remaining submission"

        self.client.logout()

        first_voter = VoterFactory(user=None)
        second_voter = VoterFactory(user=None)
        third_voter = VoterFactory(user=None)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': second_voter.email, 'zipcode': second_voter.zip
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': third_voter.email, 'zipcode': third_voter.zip
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        # Initially each submission's vote tally will include all votes that we just cast
        # plus one for the submitter
        self.assertEqual(Submission.objects.get(id=self.second_submission.id).votes, 3)
        self.assertEqual(Submission.objects.get(id=self.third_submission.id).votes, 3)

        assert self.client.login(username=self.user.username, password=self.password)
        rsp = self.client.post(self.url, data={
            "confirm": "confirm",
            "handling": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.url)

        merged = Submission.objects.get(id=self.third_submission.id)
        remaining = Submission.objects.get(id=self.second_submission.id)

        # The merged idea retains its original vote tally, and the remaining idea
        # has a new vote tally reflecting all unique voters who have voted on either
        self.assertEqual(merged.votes, 3)
        self.assertEqual(remaining.votes, 4)

        # The vote cast by second_voter has been re-cast for the remaining submission
        # and retains a pointer to its original submission for future audits
        moved_vote = Vote.objects.get(voter=second_voter)
        self.assertEqual(moved_vote.submission, remaining)
        self.assertEqual(moved_vote.original_merged_submission, merged)
        self.assertEqual(0, Vote.objects.filter(
            voter=second_voter, submission=merged).count())

        # The vote cast by first_voter on the merged idea has not been re-cast,
        # since first_voter had already cast a vote on the remaining submission
        self.assertEqual(1, Vote.objects.filter(
            voter=first_voter, submission=merged).count())
