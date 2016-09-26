import datetime

from django.test import TestCase, override_settings
from django.utils import timezone
from mock import Mock, patch

from opendebates.tests.factories import VoteFactory, SiteModeFactory
from opendebates.utils import (
    registration_needs_captcha, vote_needs_captcha, get_site_mode,
    allow_sorting_by_votes, show_question_votes, allow_voting_and_submitting_questions,
    get_local_votes_state, get_previous_debate_time
)


class TestUtils(TestCase):
    def setUp(self):
        self.site_mode = SiteModeFactory()

    def test_get_site_mode(self):
        site_mode = get_site_mode()
        self.assertEqual(site_mode, self.site_mode)

    def test_allow_sorting_by_votes(self):
        self.assertTrue(allow_sorting_by_votes())

        self.site_mode.allow_sorting_by_votes = False
        self.site_mode.save()
        self.assertFalse(allow_sorting_by_votes())

    def test_show_question_votes(self):
        self.assertTrue(show_question_votes())

        self.site_mode.show_question_votes = False
        self.site_mode.save()
        self.assertFalse(show_question_votes())

    def test_allow_voting_and_submitting_questions(self):
        self.assertTrue(allow_voting_and_submitting_questions())

        self.site_mode.allow_voting_and_submitting_questions = False
        self.site_mode.save()
        self.assertFalse(allow_voting_and_submitting_questions())

    def test_get_local_votes_state(self):
        self.assertEqual(get_local_votes_state(), 'NY')

        self.site_mode.debate_state = 'NJ'
        self.site_mode.save()
        self.assertEqual(get_local_votes_state(), 'NJ')

    def test_get_previous_debate_time(self):
        self.assertIsNone(get_previous_debate_time())

        previous_debate_time = timezone.make_aware(
            datetime.datetime(2016, 1, 1, 12)
        )
        self.site_mode.previous_debate_time = previous_debate_time
        self.site_mode.save()
        self.assertEqual(get_previous_debate_time(), previous_debate_time)


@override_settings(USE_CAPTCHA=True)
class TestCaptchaUtils(TestCase):
    def setUp(self):
        self.mock_request = Mock(spec=object)
        self.mock_request.user = Mock()
        self.mock_request.user.is_authenticated = lambda: False

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
        VoteFactory(voter__email=email)
        with patch('opendebates.utils.get_voter') as mock_get_voter:
            mock_get_voter.return_value = {'email': email}
            self.assertFalse(vote_needs_captcha(self.mock_request))
