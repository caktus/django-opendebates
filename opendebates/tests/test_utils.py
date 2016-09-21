from django.test import TestCase, override_settings
from mock import Mock, patch

from opendebates.tests.factories import VoteFactory, SiteModeFactory
from opendebates.utils import registration_needs_captcha, vote_needs_captcha


@override_settings(USE_CAPTCHA=True)
class TestCaptchaUtils(TestCase):
    def setUp(self):
        self.mock_request = Mock(spec=object)
        self.mock_request.user = Mock()
        self.mock_request.user.is_authenticated = lambda: False
        self.mock_request.site_mode = SiteModeFactory()

    def test_registration_captcha(self):
        self.assertTrue(registration_needs_captcha(self.mock_request))

    @override_settings(USE_CAPTCHA=False)
    def test_registration_captcha_disabled(self):
        self.assertFalse(registration_needs_captcha(self.mock_request))

    @override_settings(USE_CAPTCHA=False)
    def test_vote_captcha_disabled(self):
        self.assertFalse(vote_needs_captcha(self.mock_request))

    def test_vote_captcha_no_voter(self):
        # first vote requires captcha
        with patch('opendebates.utils.get_voter') as mock_get_voter:
            mock_get_voter.return_value = {}
            self.assertTrue(vote_needs_captcha(self.mock_request))

    def test_vote_captcha_first_vote(self):
        # first vote requires captcha even if voter exists
        with patch('opendebates.utils.get_voter') as mock_get_voter:
            mock_get_voter.return_value = {'email': 'nevervoted@example.com'}
            self.assertTrue(vote_needs_captcha(self.mock_request))

    def test_vote_captcha_first_vote_loggedin(self):
        # first vote does not require captcha if user is logged in
        # even if no prior votes have been cast by the logged in user
        mock_request_loggedin = Mock(spec=object)
        mock_request_loggedin.user = Mock()
        mock_request_loggedin.user.is_authenticated = lambda: True
        self.assertFalse(vote_needs_captcha(mock_request_loggedin))

    def test_vote_captcha_second_vote(self):
        # second vote does not require captcha
        email = 'hasvoted@example.com'
        VoteFactory(voter__email=email, voter__site_mode=self.mock_request.site_mode)
        with patch('opendebates.utils.get_voter') as mock_get_voter:
            mock_get_voter.return_value = {'email': email}
            self.assertFalse(vote_needs_captcha(self.mock_request))
