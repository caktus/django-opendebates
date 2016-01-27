import json

from django.test import TestCase

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
        }
        rsp = self.client.post(self.submission_url, data=data,
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, rsp.status_code)
        json_rsp = json.loads(rsp.content)
        # votes is not incremented
        refetched_sub = Submission.objects.get(pk=self.submission.pk)
        self.assertEqual(self.votes + 0, refetched_sub.votes)
        self.assertIn('That email is registered', json_rsp['errors']['email'])

    def test_vote_user(self):
        "Authenticated user can vote."
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

    def test_vote_twice_user(self):
        "Authenticated user can only vote once."
        VoteFactory(submission=self.submission, voter=self.voter)
        data = {
            'email': self.voter.email,
            'zipcode': self.voter.zip,
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
