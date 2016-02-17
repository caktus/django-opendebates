from django.test import TestCase
from mock import patch, Mock

from opendebates.context_processors import global_vars


class NumberOfVotesTest(TestCase):
    def test_number_of_votes(self):
        mock_request = Mock()
        with patch('opendebates.utils.cache') as mock_cache:
            mock_cache.get.return_value = 2
            context = global_vars(mock_request)
            self.assertEqual(2, int(context['NUMBER_OF_VOTES']))
