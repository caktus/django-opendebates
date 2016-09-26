import datetime
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from opendebates.models import Submission, Vote, SiteMode, ZipCode
from opendebates_emails.models import EmailTemplate
from .factories import CategoryFactory, UserFactory, VoterFactory, SubmissionFactory
from .utilities import patch_cache_templatetag


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
            'headline': 'Headline of my question',
            'citation': 'https://www.google.com',
        }
        EmailTemplate(type="submitted_new_idea",
                      name="Email Submitter",
                      subject="Thanks for your idea, {{ idea.voter.user.first_name }}",
                      html="Your idea was {{ idea.idea }}",
                      text="Your idea citation was {{ idea.citation }}",
                      from_email="{{ idea.voter.email }}",
                      to_email="{{ idea.voter.email }}").save()

    # failures

    def test_missing_headline(self):
        data = self.data.copy()
        del data['headline']
        rsp = self.client.post(self.url, data=data)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('headline', form.errors)
        self.assertIn('This field is required.', str(form.errors))

    def test_missing_question_not_required(self):
        data = self.data.copy()
        del data['question']
        rsp = self.client.post(self.url, data=data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)

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

    def test_citation_too_long(self):
        data = self.data.copy()
        data['citation'] = 'https://www.' + 'x' * 250 + '.com'
        rsp = self.client.post(self.url, data=data)
        form = rsp.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('citation', form.errors)
        self.assertIn('has at most 255 characters', str(form.errors))

    # success

    def test_post_submission(self):
        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)
        # Check the Submission attributes
        self.assertEqual(submission.voter, self.voter)
        self.assertEqual(submission.category, self.category)
        self.assertEqual(submission.headline, self.data['headline'])
        self.assertEqual(submission.followup, self.data['question'])
        self.assertEqual(submission.idea, u'%s %s' % (
            self.data['headline'], self.data['question']))
        self.assertEqual(submission.citation, self.data['citation'])
        self.assertEqual(submission.ip_address, '127.0.0.1')
        self.assertEqual(submission.approved, True)
        # vote count is kept on the submission model
        self.assertEqual(submission.votes, 1)
        self.assertEqual(submission.current_votes, 1)
        # but Vote objects are also created
        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))

    def test_post_submission_after_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = timezone.make_aware(
            datetime.datetime(2016, 1, 1, 12)
        )
        mode.save()

        self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        # vote count is kept on the submission model
        self.assertEqual(submission.votes, 1)
        self.assertEqual(submission.current_votes, 1)
        # but Vote objects are also created
        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))

    def test_post_submission_before_previous_debate(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.previous_debate_time = timezone.now() + datetime.timedelta(days=1)
        mode.save()

        self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        # vote count is kept on the submission model
        self.assertEqual(submission.votes, 1)
        # We haven't hit the deadline for the previous debate, so no current_vote
        self.assertEqual(submission.current_votes, 0)
        # but Vote objects are also created
        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))

    def test_post_submission_from_local_user(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.debate_state = "NY"
        mode.save()

        ZipCode.objects.create(zip="11111", city="Examplepolis", state="NY")

        user = UserFactory(password="secretpassword")
        VoterFactory(user=user, email=user.email, zip="11111", state="NY")

        self.client.logout()
        assert self.client.login(username=user.username, password="secretpassword")

        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)

        self.assertEqual(submission.votes, 1)
        self.assertEqual(submission.current_votes, 1)
        self.assertEqual(submission.local_votes, 1)

    def test_post_submission_from_nonlocal_user(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.debate_state = "FL"
        mode.save()

        ZipCode.objects.create(zip="11111", city="Examplepolis", state="NY")

        user = UserFactory(password="secretpassword")
        VoterFactory(user=user, email=user.email, zip="11111", state="NY")

        self.client.logout()
        assert self.client.login(username=user.username, password="secretpassword")

        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)

        self.assertEqual(submission.votes, 1)
        self.assertEqual(submission.current_votes, 1)
        self.assertEqual(submission.local_votes, 0)

    def test_post_submission_when_no_local_district_configured(self):
        mode, _ = SiteMode.objects.get_or_create()
        mode.debate_state = None
        mode.save()

        ZipCode.objects.create(zip="11111", city="Examplepolis", state="NY")

        user = UserFactory(password="secretpassword")
        VoterFactory(user=user, email=user.email, zip="11111", state="NY")

        self.client.logout()
        assert self.client.login(username=user.username, password="secretpassword")

        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)

        self.assertEqual(submission.votes, 1)
        self.assertEqual(submission.current_votes, 1)
        self.assertEqual(submission.local_votes, 0)

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

    def test_unmoderated_merged_question_404s(self):
        "Question page should 404 if the question has been removed as a duplicate"
        submission = SubmissionFactory()
        other_submission = SubmissionFactory()
        submission.approved = False
        submission.duplicate_of = other_submission
        submission.save()
        rsp = self.client.get(submission.get_absolute_url())
        self.assertEqual(404, rsp.status_code)

    def test_unmoderated_question_is_viewable(self):
        """
        Question page should be accessible if the question has been unmoderated,
        but with a notice of removal instead of the typical vote flag share buttons.
        """
        submission = SubmissionFactory()
        rsp = self.client.get(submission.get_absolute_url())
        self.assertNotContains(rsp, "This question has been removed.")
        self.assertContains(rsp, "Share This Question!")
        self.assertContains(rsp, "share-fb-%s" % submission.id)
        self.assertContains(rsp, '<a id="vote-button-%s"' % submission.id)
        self.assertContains(rsp, "Merge")

        submission.approved = False
        submission.save()
        rsp = self.client.get(submission.get_absolute_url())
        self.assertEqual(200, rsp.status_code)

        self.assertContains(rsp, "This question has been removed.")
        self.assertNotContains(rsp, "Share This Question!")
        self.assertNotContains(rsp, "share-fb-%s" % submission.id)
        self.assertNotContains(rsp, '<a id="vote-button-%s"' % submission.id)
        self.assertNotContains(rsp, "Merge")

    def test_questions_page_redirects(self):
        "Questions view redirects to homepage because it is only meant for form handling."
        questions_url = reverse('questions')
        rsp = self.client.get(questions_url)
        self.assertEqual(302, rsp.status_code)
        self.assertEqual("/", urlparse(rsp['Location']).path)

    def test_post_submission_with_source(self):
        "An opendebates.source cookie will be transmitted to the submission and vote."
        source = "a-source-code"
        self.client.cookies['opendebates.source'] = source
        rsp = self.client.post(self.url, data=self.data)
        submission = Submission.objects.first()
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)
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
        self.assertRedirects(
            rsp, submission.get_absolute_url() + "#created=%s" % submission.id)
        # Check the Submission attributes
        self.assertEqual(submission.voter, self.voter)
        self.assertEqual(submission.source, None)

        votes = Vote.objects.filter(voter=self.voter)
        self.assertEqual(1, len(votes))
        self.assertEqual(votes[0].source, None)


class SubmissionCacheTest(TestCase):

    def setUp(self):
        self.submission = SubmissionFactory(has_duplicates=True)

    @patch_cache_templatetag()
    def test_caching_list_first(self):
        rsp = self.client.get("/")
        self.assertNotIn('Click to see the questions that were merged into this', rsp.content)

        rsp = self.client.get(self.submission.get_absolute_url())
        self.assertIn('Click to see the questions that were merged into this', rsp.content)

    @patch_cache_templatetag()
    def test_caching_detail_first(self):
        rsp = self.client.get(self.submission.get_absolute_url())
        self.assertIn('Click to see the questions that were merged into this', rsp.content)

        rsp = self.client.get("/")
        self.assertNotIn('Click to see the questions that were merged into this', rsp.content)
