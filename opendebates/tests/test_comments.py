# from django.conf import settings
# from django.core.urlresolvers import reverse
# from django.test import TestCase
#
# from .factories import UserFactory, SubmissionFactory
# from opendebates_comments.models import Comment
#
#
# class CommentTest(TestCase):
#
#     def setUp(self):
#         self.submission = SubmissionFactory()
#         self.submission_url = self.submission.get_absolute_url()
#         self.comment_url = reverse('comment')
#         password = 'secretPassword'
#         self.user = UserFactory(password=password)
#         assert self.client.login(username=self.user.username, password=password)
#
#     def test_comment_form_anon(self):
#         "Anon users don't see comment form."
#         self.client.logout()
#         rsp = self.client.get(self.submission_url)
#         self.assertNotIn('form', rsp.context)
#
#     def test_comment_form_user(self):
#         "Authenticated users see comment form."
#         rsp = self.client.get(self.submission_url)
#         self.assertIn('form', rsp.context)
#
#     def get_initial_form_data(self):
#         "Helper to get the security features from the form before submitting."
#         rsp = self.client.get(self.submission_url)
#         form = rsp.context['form']
#         return {
#             'object_id': self.submission.pk,
#             'comment': 'My great comment',
#             'timestamp': form['timestamp'].value(),
#             'security_hash': form['security_hash'].value(),
#             'next': self.submission_url,
#         }
#
#     def test_empty_comment(self):
#         "Empty comment fails validation."
#         data = self.get_initial_form_data()
#         data['comment'] = ''
#         rsp = self.client.post(self.comment_url, data=data)
#         self.assertEqual(200, rsp.status_code)
#         self.assertIn('comment', rsp.context['form'].errors)
#
#     def test_empty_target(self):
#         "Empty target fails validation."
#         data = self.get_initial_form_data()
#         del data['object_id']
#         rsp = self.client.post(self.comment_url, data=data)
#         self.assertEqual(400, rsp.status_code)
#
#     def test_missing_timestamp(self):
#         "Missing timestamp fails security validation."
#         data = self.get_initial_form_data()
#         del data['timestamp']
#         rsp = self.client.post(self.comment_url, data=data)
#         self.assertEqual(400, rsp.status_code)
#
#     def test_missing_security_hash(self):
#         "Missing security_hash fails security validation."
#         data = self.get_initial_form_data()
#         del data['security_hash']
#         rsp = self.client.post(self.comment_url, data=data)
#         self.assertEqual(400, rsp.status_code)
#
#     def test_valid_comment(self):
#         data = self.get_initial_form_data()
#         rsp = self.client.post(self.comment_url, data=data)
#         comment = Comment.objects.first()
#         self.assertRedirects(rsp, self.submission_url + '?c={}'.format(comment.pk))
#         # comment is saved
#         self.assertEqual(comment.comment, data['comment'])
#
#     def test_anon_gets_redirected_to_login(self):
#         data = self.get_initial_form_data()
#         self.client.logout()
#         rsp = self.client.post(self.comment_url, data=data)
#         self.assertRedirects(rsp, settings.LOGIN_URL)
