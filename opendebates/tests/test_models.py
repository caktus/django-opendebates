from django.test import TestCase

from .factories import UserFactory, VoterFactory


class VoterUserDisplayNameTest(TestCase):

    def test_anonymous(self):
        voter = VoterFactory(user=None)
        self.assertEqual('Somebody', str(voter.user_display_name()))

    def test_user_blank(self):
        user = UserFactory(first_name='', last_name='')
        voter = VoterFactory(user=user)
        self.assertEqual('Somebody', str(voter.user_display_name()))

    def test_user_no_last_name(self):
        user = UserFactory(first_name='George', last_name='')
        voter = VoterFactory(user=user)
        self.assertEqual('George', str(voter.user_display_name()))

    def test_user_both_names(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user)
        self.assertEqual('George W.', str(voter.user_display_name()))

    def test_user_with_state(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, state='VA')
        self.assertEqual('George W. from VA', str(voter.user_display_name()))

    def test_user_with_explicit_display_name(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, display_name='Prez1')
        self.assertEqual('Prez1', str(voter.user_display_name()))

    def test_voter_with_explicit_display_name_with_state(self):
        user = UserFactory(first_name='George', last_name='Washington')
        voter = VoterFactory(user=user, display_name='Prez1', state='VA')
        self.assertEqual('Prez1 from VA', str(voter.user_display_name()))
