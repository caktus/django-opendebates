from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase

from .factories import UserFactory


class RegisterTest(TestCase):

    def setUp(self):
        self.url = reverse('registration_register')
        self.data = {
            'username': 'gwash',
            'password1': 'secretpassword',
            'password2': 'secretpassword',
            'first_name': 'George',
            'last_name': 'Washington',
            'email': 'gwash@example.com',
            'zip': '12345',
        }

    def test_registration_get(self):
        "GET the form successfully."
        with self.assertTemplateUsed('registration/registration_form.html'):
            rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)

    def test_post_success(self):
        "POST the form with all required values."
        home_url = reverse('list_ideas')
        rsp = self.client.post(self.url, data=self.data, follow=True)
        self.assertRedirects(rsp, home_url)
        new_user = get_user_model().objects.first()
        self.assertEqual(new_user.first_name, self.data['first_name'])

    def test_post_missing_variable(self):
        "POST with a missing required value."
        # delete each required key and POST
        for key in self.data:
            data = self.data.copy()
            del data[key]
            rsp = self.client.post(self.url)
            self.assertEqual(200, rsp.status_code)
            form = rsp.context['form']
            self.assertIn(key, form.errors)
            self.assertIn('field is required', str(form.errors))

    def test_email_must_be_unique(self):
        # case insensitive
        UserFactory(email=self.data['email'].upper())
        rsp = self.client.post(self.url, data=self.data, follow=True)
        form = rsp.context['form']
        self.assertEqual(200, rsp.status_code)
        self.assertIn('email', form.errors)
        self.assertIn('already in use', str(form.errors))

    def test_twitter_handle_gets_cleaned(self):
        "Various forms of twitter_handle entries are cleaned to canonical form."
        data = {}
        for twitter_handle in [
                '@twitter',
                'twitter',
                'https://twitter.com/twitter',
                'http://twitter.com/twitter',
                'twitter.com/twitter',
        ]:
            data['twitter_handle'] = twitter_handle
            rsp = self.client.post(self.url, data=data)
            form = rsp.context['form']
            self.assertEqual('twitter', form.cleaned_data['twitter_handle'])


class LoginLogoutTest(TestCase):

    def setUp(self):
        self.username = 'gwash'
        self.email = 'gwash@example.com'
        self.password = 'secretpassword'
        UserFactory(username=self.username,
                    email=self.email,
                    password=self.password)
        self.login_url = reverse('auth_login')
        self.home_url = reverse('list_ideas')

    def test_login_with_username(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.username, 'password': self.password, 'next': '/'}
        )
        self.assertRedirects(rsp, self.home_url)

    def test_login_with_email(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.email, 'password': self.password, 'next': '/'}
        )
        self.assertRedirects(rsp, self.home_url)

    def test_failed_login(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.username, 'password': self.password + 'bad', 'next': '/'}
        )
        self.assertEqual(200, rsp.status_code)
        form = rsp.context['form']
        self.assertIn('enter a correct username and password', str(form.errors))

    def test_logout(self):
        self.assertTrue(self.client.login(username=self.username, password=self.password))
        logout_url = reverse('auth_logout')
        with self.assertTemplateUsed('registration/logout.html'):
            rsp = self.client.get(logout_url)
        self.assertIn('Log in', rsp.content)
