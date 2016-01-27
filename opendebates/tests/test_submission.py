from django.core.urlresolvers import reverse
from django.test import TestCase

from opendebates.models import Submission, Vote
from .factories import CategoryFactory, UserFactory, VoterFactory, SubmissionFactory


class SubmissionTest(TestCase):

    def setUp(self):
        self.url = reverse('questions')
        password = 'secretpassword'
        self.user = UserFactory(password=password)
        self.voter = VoterFactory(user=self.user, email=self.user.email)
        self.category = CategoryFactory()
        assert self.client.login(username=self.user.username, password=password)
        self.data = {
            'category': self.category.pk,
            'question': 'My great question?',
            'citation': 'https://www.google.com',
        }

    # failures

    def test_missing_question(self):
        data = self.data.copy()
        del data['question']
        rsp = self.client.post(self.url, data=data)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('question', form.errors)
        self.assertIn('This field is required.', str(form.errors))

    def test_missing_category(self):
        data = self.data.copy()
        del data['category']
        rsp = self.client.post(self.url, data=data)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)
        self.assertIn('This field is required.', str(form.errors))

    def test_malformed_citation(self):
        data = self.data.copy()
        data['citation'] = 'not a URL'
        rsp = self.client.post(self.url, data=data)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('citation', form.errors)
        self.assertIn('Enter a valid URL.', str(form.errors))

    # success

    def test_post_submission(self):
        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(rsp, submission.get_absolute_url())
        # Check the Submission attributes
        self.assertEqual(submission.voter, self.voter)
        self.assertEqual(submission.category, self.category)
        self.assertEqual(submission.idea, self.data['question'])
        self.assertEqual(submission.citation, self.data['citation'])
        self.assertEqual(submission.ip_address, '127.0.0.1')
        self.assertEqual(submission.approved, True)
        # vote count is kept on the submission model
        self.assertEqual(submission.votes, 1)
        # but Vote objects are also created
        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))

    def test_post_submission_anon(self):
        "Anon user can post submissions, but needs to login/register first."
        self.client.logout()
        register_url = reverse('registration_register')
        rsp = self.client.post(self.url, data=self.data)
        # anon user gets redirected to register/login
        self.assertRedirects(rsp, register_url)
        # submitted data gets stashed in session
        self.assertIn('opendebates.stashed_submission', self.client.session)

    def test_question_detail_page_has_links(self):
        "Question page should have links to twitter and facebook"
        twitter_link = 'https://twitter.com/intent/tweet'
        facebook_link = 'https://www.facebook.com/sharer/sharer.php'
        submission = SubmissionFactory()
        rsp = self.client.get(submission.get_absolute_url())
        self.assertContains(rsp, twitter_link)
        self.assertContains(rsp, facebook_link)

    def test_browse_questions_page(self):
        "Can view questions page and a form is present."
        questions_url = reverse('questions')
        rsp = self.client.get(questions_url)
        self.assertEqual(200, rsp.status_code)
        self.assertIn('form', rsp.context)

    def test_post_submission_with_source(self):
        "An opendebates.source cookie will be transmitted to the submission and vote."
        source = "a-source-code"
        self.client.cookies['opendebates.source'] = source
        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(rsp, submission.get_absolute_url())
        # Check the Submission attributes
        self.assertEqual(submission.voter, self.voter)
        self.assertEqual(submission.source, source)

        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))
        self.assertEqual(votes[0].source, source)

    def test_post_submission_without_source(self):
        "If no opendebates.source cookie is present, vote and submission source will be None"
        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(rsp, submission.get_absolute_url())
        # Check the Submission attributes
        self.assertEqual(submission.voter, self.voter)
        self.assertEqual(submission.source, None)

        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))
        self.assertEqual(votes[0].source, None)        
