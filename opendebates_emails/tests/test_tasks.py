from django.core import mail

from django.test import TestCase

from opendebates.tests.factories import SubmissionFactory
from opendebates_emails.tasks import send_email_task
from opendebates_emails.tests.factories import EmailTemplateFactory


class EmailSendTaskTest(TestCase):
    def setUp(self):
        self.idea = SubmissionFactory(
            idea="How high is up?",
            headline="This is the headline",
            followup="This is the followup",
        )
        self.template_name = 'voted'
        EmailTemplateFactory(
            type=self.template_name,
            subject="{{ idea.headline }}",
            html="{{ idea.followup }}",
            text="{{ idea.idea }}",
            from_email="{{ idea.voter.email|safe }}",
            to_email="{{ idea.voter.email|safe }}",
        )

    def test_it(self):
        send_email_task(self.template_name, self.idea.pk)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, self.idea.headline)
        self.assertEqual(msg.alternatives[0][0], self.idea.followup)
        self.assertEqual(msg.body, self.idea.idea)
        self.assertEqual(msg.from_email, self.idea.voter.email)
        self.assertEqual(msg.recipients(), [self.idea.voter.email])

    def test_no_template(self):
        # Should NOT raise an exception, but no email of course
        send_email_task('no_such_template', self.idea.pk)
        self.assertFalse(mail.outbox)

    def test_no_such_idea(self):
        # Should NOT raise an exception, but no email of course
        send_email_task(self.template_name, 999)
        self.assertFalse(mail.outbox)
