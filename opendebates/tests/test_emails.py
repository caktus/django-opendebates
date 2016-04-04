from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from django.core import mail
from opendebates_emails.models import EmailTemplate

from .factories import CategoryFactory, UserFactory, VoterFactory


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailTest(TestCase):
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

    def test_submission_sends_email(self):
        "After submitting a question, an email is sent from a template with `idea` context"
        EmailTemplate(type="submitted_new_idea",
                      name="Email Submitter",
                      subject="Thanks for your idea, {{ idea.voter.user.first_name }}",
                      html="Your idea was {{ idea.idea }}",
                      text="Your idea citation was {{ idea.citation }}",
                      from_email="{{ idea.voter.email }}",
                      to_email="{{ idea.voter.email }}").save()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(self.url, data=self.data)
        self.assertEqual(1, len(mail.outbox))

        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "Thanks for your idea, %s" % self.user.first_name)
        self.assertEqual(msg.alternatives[0][0], "Your idea was %s" % '%s %s' % (self.data['headline'], self.data['question']))
        self.assertEqual(msg.body,
                         "Your idea citation was %s" % self.data['citation'])
        self.assertEqual(msg.from_email, self.voter.email)
        self.assertEqual(msg.recipients(), [self.voter.email])

    def test_multiple_email_template_picks_one(self):
        "If multiple email templates exist for the same type, only one is chosen at random"
        EmailTemplate(type="submitted_new_idea",
                      name="Email Submitter",
                      subject="Thanks for your idea, {{ idea.voter.user.first_name }}",
                      html="Your idea was {{ idea.idea }}",
                      text="Your idea citation was {{ idea.citation }}",
                      from_email="{{ idea.voter.email }}",
                      to_email="{{ idea.voter.email }}").save()

        EmailTemplate(type="submitted_new_idea",
                      name="Email Submitter variation #2",
                      subject="Thanks for your idea!",
                      html="Your idea was {{ idea.idea }}",
                      text="Your idea citation was {{ idea.citation }}",
                      from_email="{{ idea.voter.email }}",
                      to_email="{{ idea.voter.email }}").save()

        self.assertEqual(0, len(mail.outbox))
        self.client.post(self.url, data=self.data)
        self.assertEqual(1, len(mail.outbox))
