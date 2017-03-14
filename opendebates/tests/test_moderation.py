from httplib import FORBIDDEN, NOT_FOUND, OK
import json
import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.models import Submission, Vote, Flag
from .factories import (UserFactory, VoterFactory, SubmissionFactory, RemovalFlagFactory,
                        MergeFlagFactory, SiteFactory, SiteModeFactory)
from .utilities import reset_session


class ModerationTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.first_submission = SubmissionFactory()
        self.second_submission = SubmissionFactory()
        self.third_submission = SubmissionFactory()

        self.preview_url = reverse('moderation_preview', kwargs={'prefix': self.mode.prefix})
        self.merge_url = reverse('moderation_merge', kwargs={'prefix': self.mode.prefix})
        self.remove_url = reverse('moderation_remove', kwargs={'prefix': self.mode.prefix})
        self.moderation_home_url = reverse('moderation_home', kwargs={'prefix': self.mode.prefix})
        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=self.password)
        os.environ['NORECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        Site.objects.clear_cache()
        del os.environ['NORECAPTCHA_TESTING']

    def test_redirects_to_login(self):
        login_url = settings.LOGIN_URL + '?next=' + self.preview_url
        self.client.logout()
        rsp = self.client.get(self.preview_url)
        self.assertRedirects(rsp, login_url)

    def test_nonsuperuser_403(self):
        self.user.is_superuser = False
        self.user.save()
        rsp = self.client.get(self.preview_url)
        self.assertEqual(FORBIDDEN, rsp.status_code)

    def test_get(self):
        rsp = self.client.get(self.preview_url)
        self.assertContains(rsp, 'Preview Moderation')

    def test_get_with_initial(self):
        rsp = self.client.get(self.preview_url + "?to_remove=10")
        self.assertContains(rsp, 'name="to_remove" type="number" value="10"')

    def test_merge_submission(self):
        self.assertEqual(self.second_submission.has_duplicates, False)
        self.assertEqual(self.second_submission.duplicate_of, None)
        self.assertEqual(self.second_submission.keywords, None)
        self.assertEqual(self.third_submission.has_duplicates, False)
        self.assertEqual(self.third_submission.duplicate_of, None)
        self.assertEqual(self.third_submission.keywords, None)

        rsp = self.client.post(self.merge_url, data={
            "action": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.moderation_home_url)

        merged = Submission.objects.get(id=self.third_submission.id)
        remaining = Submission.objects.get(id=self.second_submission.id)

        # The merged submission should now be marked as a duplicate
        self.assertEqual(merged.duplicate_of, remaining)
        self.assertIsNotNone(merged.moderated_at)

        # The remaining submission should now be marked as having duplicates
        self.assertEqual(remaining.has_duplicates, True)

        # The merged submission's content is copied into the remaining one's keywords
        self.assertIn(merged.idea, remaining.keywords)

        # Viewing the merged submission now lands visitors on the remaining submission
        # with a fragment referring to the merged submission's place on the page
        rsp = self.client.get(merged.get_absolute_url())
        self.assertRedirects(
            rsp,
            reverse('show_idea', args=[self.mode.prefix, remaining.id]) + (
                "#i%s" % merged.id)
        )

    def test_nested_merge_submission(self):
        self.client.post(self.merge_url, data={
            "action": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.client.post(self.merge_url, data={
            "action": "merge",
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

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': second_voter.email, 'zipcode': second_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': third_voter.email, 'zipcode': third_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        # Initially each submission's vote tally will include all votes that we just cast
        # plus one for the submitter
        self.assertEqual(Submission.objects.get(id=self.second_submission.id).votes, 3)
        self.assertEqual(Submission.objects.get(id=self.third_submission.id).votes, 3)

        assert self.client.login(username=self.user.username, password=self.password)
        rsp = self.client.post(self.merge_url, data={
            "action": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.moderation_home_url)

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

    def test_local_votes_tally_updates_after_merge(self):
        "During a merge, only unique votes get moved over to the remaining submission"

        self.client.logout()

        nonlocal_voter = VoterFactory(user=None, state="NY")
        first_local_voter = VoterFactory(user=None, state="FL")
        second_local_voter = VoterFactory(user=None, state="FL")

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': nonlocal_voter.email, 'zipcode': nonlocal_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': first_local_voter.email, 'zipcode': first_local_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': first_local_voter.email, 'zipcode': first_local_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': second_local_voter.email, 'zipcode': second_local_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        self.assertEqual(Submission.objects.get(id=self.second_submission.id).local_votes,
                         1)
        self.assertEqual(Submission.objects.get(id=self.third_submission.id).local_votes,
                         2)

        assert self.client.login(username=self.user.username, password=self.password)
        rsp = self.client.post(self.merge_url, data={
            "action": "merge",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.moderation_home_url)

        merged = Submission.objects.get(id=self.third_submission.id)
        remaining = Submission.objects.get(id=self.second_submission.id)

        # The merged idea retains its original vote tally, and the remaining idea
        # has a new vote tally reflecting all unique local voters who have voted on either
        self.assertEqual(merged.local_votes, 2)
        self.assertEqual(remaining.local_votes, 2)

    def test_unmoderate_does_not_merge_votes(self):
        "During a duplicate unmoderate, no vote merging occurs"

        self.client.logout()

        first_voter = VoterFactory(user=None)
        second_voter = VoterFactory(user=None)
        third_voter = VoterFactory(user=None)

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.third_submission.get_absolute_url(), data={
            'email': second_voter.email, 'zipcode': second_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': first_voter.email, 'zipcode': first_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        reset_session(self.client)

        rsp = self.client.post(self.second_submission.get_absolute_url(), data={
            'email': third_voter.email, 'zipcode': third_voter.zip,
            'g-recaptcha-response': 'PASSED'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual("200", json.loads(rsp.content)['status'])

        # Initially each submission's vote tally will include all votes that we just cast
        # plus one for the submitter
        self.assertEqual(Submission.objects.get(id=self.second_submission.id).votes, 3)
        self.assertEqual(Submission.objects.get(id=self.third_submission.id).votes, 3)

        assert self.client.login(username=self.user.username, password=self.password)
        rsp = self.client.post(self.merge_url, data={
            "action": "unmoderate",
            "to_remove": self.third_submission.id,
            "duplicate_of": self.second_submission.id,
        })
        self.assertRedirects(rsp, self.moderation_home_url)

        merged = Submission.objects.get(id=self.third_submission.id)
        remaining = Submission.objects.get(id=self.second_submission.id)

        # Both ideas retain their original vote tallies
        self.assertEqual(merged.votes, 3)
        self.assertEqual(remaining.votes, 3)

        # And vote objects are untouched
        moved_vote = Vote.objects.get(voter=second_voter)
        self.assertEqual(moved_vote.submission, merged)
        self.assertEqual(moved_vote.original_merged_submission, None)
        self.assertEqual(0, Vote.objects.filter(
            voter=second_voter, submission=remaining).count())

        # But the duplicate submission is now unavailable & has been marked as duplicate
        self.assertEqual(False, merged.approved)
        self.assertEqual(remaining, merged.duplicate_of)

        # Meanwhile the remaining submission has no direct record of the merge into it
        self.assertEqual(False, remaining.has_duplicates)

        rsp = self.client.get(merged.get_absolute_url())
        self.assertEqual(NOT_FOUND, rsp.status_code)

    def test_merge_link_hidden_after_merge(self):
        merge_url = reverse('merge', args=[self.mode.prefix, self.first_submission.pk])
        rsp = self.client.get(self.first_submission.get_absolute_url())
        self.assertContains(rsp, merge_url)
        self.first_submission.duplicate_of = self.second_submission
        self.first_submission.save()
        self.second_submission.has_duplicates = True
        self.second_submission.save()
        rsp = self.client.get(self.first_submission.get_absolute_url(), follow=True)
        self.assertNotContains(rsp, merge_url)

    def test_remove_submission(self):
        data = {
            'to_remove': self.first_submission.pk,
            'duplicate_of': '',
            'action': 'remove',
        }
        rsp = self.client.post(self.remove_url, data=data)
        self.assertRedirects(rsp, self.moderation_home_url)
        refetched_sub = Submission.objects.get(pk=self.first_submission.pk)
        self.assertFalse(refetched_sub.approved)
        self.assertIsNotNone(refetched_sub.moderated_at)

    def test_reject_merge(self):
        # pretend a user created a merge flag
        flag = MergeFlagFactory(to_remove=self.first_submission,
                                duplicate_of=self.second_submission)
        # now let's reject the merge
        data = {
            'to_remove': self.first_submission.pk,
            'duplicate_of': self.second_submission.pk,
            'action': 'reject',
        }
        rsp = self.client.post(self.merge_url, data=data)
        self.assertRedirects(rsp, self.moderation_home_url)
        refetched_sub1 = Submission.objects.get(pk=self.first_submission.pk)
        refetched_sub2 = Submission.objects.get(pk=self.second_submission.pk)
        self.assertEqual(refetched_sub1.duplicate_of, None)
        self.assertEqual(refetched_sub2.has_duplicates, False)
        # and Flag is now marked reviewed
        refetched_flag = Flag.objects.get(pk=flag.pk)
        self.assertEqual(refetched_flag.reviewed, True)

    def test_preview_missing_submission(self):
        data = {
            'to_remove': ''
        }
        rsp = self.client.post(self.preview_url, data=data)
        self.assertEqual(OK, rsp.status_code)
        self.assertIn('This field is required', str(rsp.context['form'].errors))

    def test_preview_bad_submissions(self):
        data = {
            'to_remove': self.first_submission.pk,
            'duplicate_of': self.second_submission.pk
        }
        self.first_submission.delete()
        self.second_submission.delete()
        rsp = self.client.post(self.preview_url, data=data)
        self.assertEqual(OK, rsp.status_code)
        self.assertIn('submission does not exist', rsp.context['form'].errors['to_remove'][0])
        self.assertIn('submission does not exist', rsp.context['form'].errors['duplicate_of'][0])

    def test_preview_must_be_different_submissions(self):
        data = {
            'to_remove': self.first_submission.pk,
            'duplicate_of': self.first_submission.pk
        }
        rsp = self.client.post(self.preview_url, data=data)
        self.assertEqual(OK, rsp.status_code)
        self.assertIn('Cannot merge a submission into itself', str(rsp.context['form'].errors))


class ModerationHomeTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=self.password)
        self.url = reverse('moderation_home', kwargs={'prefix': self.mode.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_redirects_to_login(self):
        login_url = settings.LOGIN_URL + '?next=' + self.url
        self.client.logout()
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, login_url)

    def test_nonsuperuser_403(self):
        self.user.is_superuser = False
        self.user.save()
        rsp = self.client.get(self.url)
        self.assertEqual(FORBIDDEN, rsp.status_code)

    def test_removal_flags_queryset(self):
        # these submissions should not be on our page
        submission_without_flag = SubmissionFactory()
        submission_with_merge_flag = SubmissionFactory()
        MergeFlagFactory(duplicate_of=submission_with_merge_flag)
        submission_already_moderated = SubmissionFactory(moderated_removal=True)
        RemovalFlagFactory(to_remove=submission_already_moderated)

        # these submissions should be on our page
        flagged_submission_1 = SubmissionFactory()
        RemovalFlagFactory(to_remove=flagged_submission_1)
        flagged_submission_2 = SubmissionFactory()
        RemovalFlagFactory.create_batch(to_remove=flagged_submission_2, size=2)

        rsp = self.client.get(self.url)
        self.assertEqual(OK, rsp.status_code)
        qs = rsp.context['flagged_for_removal']
        self.assertNotIn(submission_without_flag, qs)
        self.assertNotIn(submission_with_merge_flag, qs)
        self.assertNotIn(submission_already_moderated, qs)
        self.assertIn(flagged_submission_1, qs)
        self.assertIn(flagged_submission_2, qs)
        # qs is ordered by flag count descending
        self.assertEqual([flagged_submission_2, flagged_submission_1], list(qs))

    def test_merge_flags(self):
        removal_flag = RemovalFlagFactory()
        already_reviewed_flag = MergeFlagFactory(reviewed=True)
        merge_flags = MergeFlagFactory.create_batch(size=3)
        rsp = self.client.get(self.url)
        self.assertEqual(OK, rsp.status_code)
        qs = rsp.context['merge_flags']
        self.assertNotIn(removal_flag, qs)
        self.assertNotIn(already_reviewed_flag, qs)
        self.assertEqual(set(merge_flags), set(qs))


class RemovalFlagTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.submission = SubmissionFactory()
        self.url = reverse('report', args=[self.mode.prefix, self.submission.pk])
        self.login_url = settings.LOGIN_URL + '?next=' + self.url
        password = 'secretPassword'
        self.user = UserFactory(password=password)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=password)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, self.login_url)

    def test_get_report_page(self):
        rsp = self.client.get(self.url)
        self.assertContains(rsp, self.submission.headline)
        self.assertContains(rsp, self.submission.followup)

    def test_report_missing_submission_fails(self):
        self.submission.delete()
        rsp = self.client.get(self.url)
        self.assertEqual(NOT_FOUND, rsp.status_code)

    def test_report_is_successful(self):
        rsp = self.client.post(self.url)
        self.assertRedirects(rsp, self.submission.get_absolute_url())
        flag = Flag.objects.get(to_remove=self.submission)
        self.assertEqual(flag.voter, self.voter)
        self.assertEqual(flag.duplicate_of, None)

    def test_duplicate_report_ok_but_only_1_flag_created(self):
        RemovalFlagFactory(to_remove=self.submission, voter=self.voter)
        rsp = self.client.post(self.url)
        self.assertRedirects(rsp, self.submission.get_absolute_url())
        count = Flag.objects.filter(to_remove=self.submission).count()
        self.assertEqual(1, count)


class MergeFlagTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.mode = SiteModeFactory(site=self.site)

        self.submission = SubmissionFactory()
        self.url = reverse('merge', args=[self.mode.prefix, self.submission.pk])
        self.login_url = reverse('auth_login', args=[self.mode.prefix]) + '?next=' + self.url
        password = 'secretPassword'
        self.user = UserFactory(password=password)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=password)

    def tearDown(self):
        Site.objects.clear_cache()

    def test_login_required(self):
        self.client.logout()
        rsp = self.client.get(self.url)
        self.assertRedirects(rsp, self.login_url)

    def test_get_merge_page(self):
        rsp = self.client.get(self.url)
        self.assertContains(rsp, self.submission.headline)
        self.assertContains(rsp, self.submission.followup)

    def test_merge_missing_submission_fails(self):
        self.submission.delete()
        rsp = self.client.get(self.url)
        self.assertEqual(NOT_FOUND, rsp.status_code)

    def test_merge_is_successful(self):
        duplicate_of = SubmissionFactory()
        data = {
            'duplicate_of_url': 'https://example.com' + duplicate_of.get_absolute_url()
        }
        rsp = self.client.post(self.url, data=data)
        self.assertRedirects(rsp, self.submission.get_absolute_url())
        flag = Flag.objects.get(to_remove=self.submission)
        self.assertEqual(flag.voter, self.voter)
        self.assertEqual(flag.duplicate_of, duplicate_of)

    def test_merge_is_successful_with_show_idea_url(self):
        duplicate_of = SubmissionFactory()
        show_idea_url = reverse('show_idea', args=[self.mode.prefix, duplicate_of.pk])
        data = {
            'duplicate_of_url': 'https://example.com' + show_idea_url
        }
        rsp = self.client.post(self.url, data=data)
        self.assertRedirects(rsp, self.submission.get_absolute_url())
        flag = Flag.objects.get(to_remove=self.submission)
        self.assertEqual(flag.voter, self.voter)
        self.assertEqual(flag.duplicate_of, duplicate_of)

    def test_duplicate_merge_redirects_but_only_1_flag_created(self):
        MergeFlagFactory(to_remove=self.submission, voter=self.voter)
        duplicate_of = SubmissionFactory()
        data = {
            'duplicate_of_url': 'https://example.com' + duplicate_of.get_absolute_url()
        }
        rsp = self.client.post(self.url, data=data)
        self.assertRedirects(rsp, self.submission.get_absolute_url())
        count = Flag.objects.filter(to_remove=self.submission).count()
        self.assertEqual(1, count)

    def test_malformed_url(self):
        data = {
            'duplicate_of_url': 'this is totally not a URL'
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(OK, rsp.status_code)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('Enter a valid URL', str(form.errors))
        self.assertFalse(Flag.objects.exists())

    def test_valid_url_but_404(self):
        data = {
            'duplicate_of_url': 'https://example.com/questions/what/vote/'
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(OK, rsp.status_code)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('not the URL of a question', str(form.errors))
        self.assertFalse(Flag.objects.exists())

    def test_valid_url_but_not_a_question_url(self):
        data = {
            'duplicate_of_url': 'https://example.com/questions/'
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(OK, rsp.status_code)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('not the URL of a question', str(form.errors))
        self.assertFalse(Flag.objects.exists())

    def test_cant_merge_same_submission_into_itself(self):
        data = {
            'duplicate_of_url': 'https://example.com' + self.submission.get_absolute_url()
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(OK, rsp.status_code)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('not the URL of this submission', str(form.errors))
        self.assertFalse(Flag.objects.exists())

    def test_cant_merge_into_unapproved_submission(self):
        duplicate_of = SubmissionFactory(approved=False)
        data = {
            'duplicate_of_url': 'https://example.com' + duplicate_of.get_absolute_url()
        }
        rsp = self.client.post(self.url, data=data)
        self.assertEqual(OK, rsp.status_code)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid Question URL', str(form.errors))
        self.assertFalse(Flag.objects.exists())
