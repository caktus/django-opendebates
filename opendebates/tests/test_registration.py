from functools import partial
import os

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

from .factories import UserFactory, VoterFactory, SiteFactory, DebateFactory


# Force the reverse() used here in the tests to always use the full
# urlconf, despite whatever machinations have taken place due to the
# DebateMiddleware.
old_reverse = reverse
reverse = partial(old_reverse, urlconf='opendebates.urls')


class RegisterTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.url = reverse('registration_register', kwargs={'prefix': self.debate.prefix})
        self.data = {
            'username': 'gwash',
            'password1': 'secretpassword',
            'password2': 'secretpassword',
            'first_name': 'George',
            'last_name': 'Washington',
            'email': 'gwash@example.com',
            'zip': '12345',
            'g-recaptcha-response': 'PASSED'
        }
        os.environ['NORECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        Site.objects.clear_cache()
        os.environ.pop('NORECAPTCHA_TESTING', '')

    def test_registration_get(self):
        "GET the form successfully."
        with self.assertTemplateUsed('registration/registration_form.html'):
            rsp = self.client.get(self.url)
        self.assertEqual(200, rsp.status_code)

    def test_toggle_form_display_name(self):
        with override_settings(ENABLE_USER_DISPLAY_NAME=True):
            rsp = self.client.get(self.url)
            self.assertContains(rsp, 'Display name')

        with override_settings(ENABLE_USER_DISPLAY_NAME=False):
            rsp = self.client.get(self.url)
            self.assertNotContains(rsp, 'Display name')

    def test_toggle_form_phone_number(self):
        with override_settings(ENABLE_USER_PHONE_NUMBER=True):
            rsp = self.client.get(self.url)
            self.assertContains(rsp, 'Phone number')

        with override_settings(ENABLE_USER_PHONE_NUMBER=False):
            rsp = self.client.get(self.url)
            self.assertNotContains(rsp, 'Phone number')

    def test_post_success(self):
        "POST the form with all required values."
        home_url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})
        rsp = self.client.post(self.url, data=self.data, follow=True)
        self.assertRedirects(rsp, home_url)
        new_user = get_user_model().objects.first()
        self.assertEqual(new_user.first_name, self.data['first_name'])

    def test_post_missing_variable(self):
        "POST with a missing required value."
        # delete each required key and POST
        for key in self.data:
            if key == 'g-recaptcha-response':
                continue
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
        rsp = self.client.post(self.url, data=self.data)
        self.assertRedirects(rsp, reverse('registration_duplicate',
                                          kwargs={'prefix': self.debate.prefix}))

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

    @override_settings(USE_CAPTCHA=False)
    def test_disabling_captcha(self):
        del self.data['g-recaptcha-response']
        del os.environ['NORECAPTCHA_TESTING']
        home_url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})
        rsp = self.client.post(self.url, data=self.data, follow=True)
        self.assertRedirects(rsp, home_url)
        new_user = get_user_model().objects.first()
        self.assertEqual(new_user.first_name, self.data['first_name'])


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.site = SiteFactory()
        self.debate = DebateFactory(site=self.site)

        self.username = 'gwash'
        self.email = 'gwash@example.com'
        self.password = 'secretpassword'
        # use VoterFactory so we have a Debate to authenticate against in
        # our custom auth backend when logging in via email
        self.voter = VoterFactory(
            user__username=self.username,
            user__email=self.email,
            user__password=self.password,
        )
        self.login_url = reverse('auth_login', kwargs={'prefix': self.debate.prefix})
        self.home_url = reverse('list_ideas', kwargs={'prefix': self.debate.prefix})

    def tearDown(self):
        Site.objects.clear_cache()

    def test_login_with_username(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.username, 'password': self.password,
                  'next': '/{}/'.format(self.debate.prefix)}
        )
        self.assertRedirects(rsp, self.home_url)

    def test_login_with_email(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.email, 'password': self.password,
                  'next': '/{}/'.format(self.debate.prefix)}
        )
        self.assertRedirects(rsp, self.home_url)

    def test_failed_login(self):
        rsp = self.client.post(
            self.login_url,
            data={'username': self.username, 'password': self.password + 'bad',
                  'next': '/{}/'.format(self.debate.prefix)}
        )
        self.assertEqual(200, rsp.status_code)
        form = rsp.context['form']
        self.assertIn('enter a correct username and password', str(form.errors))

    def test_logout(self):
        self.assertTrue(self.client.login(username=self.username, password=self.password))
        logout_url = reverse('auth_logout', kwargs={'prefix': self.debate.prefix})
        rsp = self.client.get(logout_url)
        self.assertEqual(200, rsp.status_code)
        self.assertEqual('Logged out', rsp.context_data['title'])
        rsp = self.client.get(self.home_url)
        self.assertIn('Log in', rsp.content)
