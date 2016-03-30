import json
import os

from django.test import TestCase
from django.test.utils import override_settings

from opendebates.models import Submission, Vote, Voter
from .factories import UserFactory, SubmissionFactory, VoterFactory, VoteFactory


class VoteTest(TestCase):

    def setUp(self):
        self.submission = SubmissionFactory()
        self.submission_url = self.submission.get_absolute_url()
        # keep track of vote count before test starts
        self.votes = self.submission.votes
        password = 'secretPassword'
        self.user = UserFactory(password=password)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        assert self.client.login(username=self.user.username, password=password)
        os.environ['NORECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        del os.environ['NORECAPTCHA_TESTING']

    # tests are all done as AJAX, like the actual site

    def test_vote_fail_anon(self):
        "Unauthenticated user vote gets validated."
        self.client.logout()
        rsp = self.client.post(self.submission_url, data={},
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        self.assertIn('email', json_rsp['errors'])
        self.assertIn('zipcode', json_rsp['errors'])
        self.assertIn('This field is required.', rsp.content)

    def test_submission_must_exist_anon(self):
        "Return 404 if submission is not present."
        self.submission.delete()
        self.client.logout()
        data = {
            'email': 'anon@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(404, rsp.status_code)

    def test_submission_must_be_approved_anon(self):
        "Return 404 if submission is not approved."
        self.submission.approved = False
        self.submission.save()
        self.client.logout()
        data = {
            'email': 'anon@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(404, rsp.status_code)

    def test_vote_anon(self):
        "Unauthenticated user successful vote."
        self.client.logout()
        data = {
            'email': 'anon@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # vote is incremented (in the JSON response)
        self.assertEqual(self.votes + 1, json_rsp['tally'])
        # .. and in the database
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.votes + 1, refetched_sub.votes)

    def test_vote_anon_new_voter_source(self):
        "New anon user with a opendebates.source cookie transmits source to vote and voter."
        self.client.logout()

        data = {
            'email': 'anon_new_voter_source@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        self.assertEqual(0, Voter.objects.filter(email=data['email']).count())

        source = 'my-source-code'
        self.client.cookies['opendebates.source'] = source

        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)

        vote = Vote.objects.get(submission=self.submission, voter__email=data['email'])
        self.assertEqual(source, vote.source)

        voter = Voter.objects.get(email=data['email'])
        self.assertEqual(source, voter.source)

    def test_vote_anon_existing_voter_source(self):
        "Existing unauthenticated user with a source cookie transmits source to vote only."
        self.client.logout()

        data = {
            'email': 'anon_existing_voter_source@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }

        anon_voter = VoterFactory(email=data['email'], user=None)
        self.assertEqual(None, anon_voter.source)

        source = 'this-source-code'
        self.client.cookies['opendebates.source'] = source

        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)

        vote = Vote.objects.get(submission=self.submission, voter__email=data['email'])
        self.assertEqual(source, vote.source)

        voter = Voter.objects.get(email=data['email'])
        self.assertEqual(None, voter.source)

    def test_vote_twice_anon(self):
        "Unauthenticated user can only vote once on a submission."
        self.client.logout()
        data = {
            'email': 'anon@example.com',
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        # create an unauthed vote (which requires an unauthed Voter object)
        anon_voter = VoterFactory(email=data['email'], user=None)
        VoteFactory(submission=self.submission, voter=anon_voter)
        # now try to vote again
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        # votes is not incremented (in JSON response or in DB)
        self.assertEqual(self.votes + 0, json_rsp['tally'])
        self.assertEqual(self.votes + 0, refetched_sub.votes)

    def test_anon_cant_use_other_users_account(self):
        "Unauthenticated cannot use an authenticated user's account."
        self.client.logout()
        data = {
            'email': self.user.email,
            'zipcode': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # votes is not incremented
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.votes + 0, refetched_sub.votes)
        self.assertIn('That email is registered', json_rsp['errors']['email'][0])

    def test_vote_user(self):
        "Authenticated user can vote."
        data = {
            'email': self.voter.email,
            'zipcode': self.voter.zip,
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # vote is incremented in JSON response
        self.assertEqual(self.votes + 1, json_rsp['tally'])
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        # ... and in DB
        self.assertEqual(self.votes + 1, refetched_sub.votes)

    def test_vote_twice_user(self):
        "Authenticated user can only vote once."
        VoteFactory(submission=self.submission, voter=self.voter)
        data = {
            'email': self.voter.email,
            'zipcode': self.voter.zip,
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # vote is not incremented in JSON response
        self.assertEqual(self.votes + 0, json_rsp['tally'])
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        # ... or in the DB
        self.assertEqual(self.votes + 0, refetched_sub.votes)

    def test_vote_user_bad_captcha(self):
        # If captcha doesn't pass, no vote
        self.client.logout()
        data = {
            'email': self.voter.email,
            'zipcode': self.voter.zip,
            'g-recaptcha-response': 'FAILED'
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.votes, refetched_sub.votes)

    @override_settings(USE_CAPTCHA=False)
    def test_vote_user_disabled_captcha(self):
        # If captcha disabled, no need for field
        data = {
            'email': self.voter.email,
            'zipcode': self.voter.zip,
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # vote is incremented in JSON response
        self.assertEqual(self.votes + 1, json_rsp['tally'])
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        # ... and in DB
        self.assertEqual(self.votes + 1, refetched_sub.votes)

    # non AJAX tests

    def test_vote_email_should_match_user(self):
        "If user bypasses our web interface and directly POSTs, we should not 500."
        data = {
            'email': 'not-the-users-email@example.com',
            'zipcode': self.voter.zip,
            'g-recaptcha-response': 'PASSED'
        }
        rsp = self.client.post(self.submission_url, data=data)
        self.assertEqual(400, rsp.status_code)
