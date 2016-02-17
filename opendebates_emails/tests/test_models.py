from django.test import TestCase
from mock import patch

from opendebates.tests.factories import SubmissionFactory
from opendebates_emails.models import send_email
from opendebates_emails.tests.factories import EmailTemplateFactory


@patch('opendebates_emails.models.send_email_task')
class EmailTemplateTestCase(TestCase):
    def setUp(self):
        self.idea = SubmissionFactory()
        self.ctx = {'idea': self.idea}
        self.type = 'template_name'
        EmailTemplateFactory(type=self.type)

    def test_sends_in_background(self, mock_task):
        send_email(self.type, self.ctx)
        mock_task.delay.assert_called_with(self.type, self.idea.pk)

    def test_ctx_no_idea(self, mock_task):
        send_email(self.type, {})
        self.assertFalse(mock_task.called)

    def test_ctx_not_submission(self, mock_task):
        send_email(self.type, {'idea': "String not Submission object"})
        self.assertFalse(mock_task.called)

    def test_no_such_template(self, mock_task):
        send_email("no_such", self.ctx)
        self.assertFalse(mock_task.called)
