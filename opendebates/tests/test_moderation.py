from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.models import Submission
from .factories import UserFactory, VoterFactory, SubmissionFactory


class ModerationTest(TestCase):

    def setUp(self):
        self.first_submission = SubmissionFactory()
        self.second_submission = SubmissionFactory()
        self.third_submission = SubmissionFactory()
        self.url = reverse('moderation_mark_duplicate')
        password = 'secretpassword'
        self.user = UserFactory(password=password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=password)

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
