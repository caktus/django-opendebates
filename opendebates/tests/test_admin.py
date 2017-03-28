from functools import partial

from django.contrib.admin.sites import AdminSite
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import patch

from opendebates.admin import SubmissionAdmin
from opendebates.models import Submission
from opendebates.tests.factories import SubmissionFactory, UserFactory, SiteModeFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# SiteModeMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


# mock objects to make the admin think we're superusers.
# mostly copied from
# https://github.com/django/django/blob/master/tests/modeladmin/tests.py#L23-L32

class MockRequest(object):
    POST = {}
    META = {}
    scheme = 'http'


class MockSuperUser(object):
    def has_perm(self, perm):
        return True

    def is_authenticated(self):
        return True


class RemoveSubmissionsTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = SubmissionAdmin(Submission, self.site)
        self.password = 'secretpassword'
        self.user = UserFactory(password=self.password, is_staff=True, is_superuser=True)
        assert self.client.login(username=self.user.username, password=self.password)
        self.submission = SubmissionFactory()
        self.queryset = Submission.objects.all()
        self.changelist_url = reverse('admin:opendebates_submission_changelist')

    def tearDown(self):
        Site.objects.clear_cache()

    def test_get(self):
        """
        GETting the intermediate page should have specified text and the PK of
        the chosen submissions.
        """
        request = MockRequest()
        request.user = MockSuperUser()
        request.site_mode = SiteModeFactory()

        rsp = self.admin.remove_submissions(request, self.queryset)
        self.assertEqual(rsp.status_code, 200)
        self.assertContains(rsp, 'remove the selected submissions?')
        self.assertContains(rsp, self.submission.pk)

    @patch('opendebates.admin.send_email')
    def test_post(self, mock_send_email):
        """
        POSTing the form should cause submissions to be removed and email to be
        sent.
        """
        data = {
            'post': 'Yes',
            'action': 'remove_submissions',
            '_selected_action': [self.submission.pk, ]
        }
        rsp = self.client.post(self.changelist_url, data=data)
        self.assertRedirects(rsp, self.changelist_url)
        # Now submission should not be approved
        submission = Submission.objects.get()
        self.assertFalse(submission.approved)
        # and 1 email should have been sent
        self.assertEqual(mock_send_email.call_count, 1)

        submission = Submission.objects.get(id=self.submission.pk)
        self.assertIsNotNone(submission.moderated_at)

    @patch('opendebates.admin.send_email')
    def test_post_multiple(self, mock_send_email):
        "POSTing multiple submissions works as well."
        data = {
            'post': 'Yes',
            'action': 'remove_submissions',
            '_selected_action': [SubmissionFactory().pk, SubmissionFactory().pk]
        }
        rsp = self.client.post(self.changelist_url, data=data)
        self.assertRedirects(rsp, self.changelist_url)
        removed_submissions = Submission.objects.filter(approved=False)
        self.assertEqual(removed_submissions.count(), 2)
        sub1, sub2 = removed_submissions
        self.assertIsNotNone(sub1.moderated_at)
        self.assertIsNotNone(sub2.moderated_at)
        untouched_submission = Submission.objects.filter(approved=True)
        self.assertEqual(untouched_submission.count(), 1)
        # and 2 emails have been sent
        self.assertEqual(mock_send_email.call_count, 2)

    @patch('opendebates.admin.send_email')
    def test_dont_send_email_if_already_unapproved(self, mock_send_email):
        "If submission was already unapproved, don't bug the user again."
        data = {
            'post': 'Yes',
            'action': 'remove_submissions',
            '_selected_action': [SubmissionFactory(approved=False).pk]
        }
        rsp = self.client.post(self.changelist_url, data=data)
        self.assertRedirects(rsp, self.changelist_url)
        removed_submissions = Submission.objects.filter(approved=False)
        self.assertEqual(removed_submissions.count(), 1)
        # and ZERO emails have been sent
        self.assertEqual(mock_send_email.call_count, 0)
