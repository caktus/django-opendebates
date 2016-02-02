from django.core.cache import cache
from django.test import TestCase

from opendebates.context_processors import global_vars
from opendebates.models import NUMBER_OF_VOTES_CACHE_ENTRY


class NumberOfVotesTest(TestCase):
    def test_number_of_votes(self):
        cache.set(NUMBER_OF_VOTES_CACHE_ENTRY, 2)
        context = global_vars(None)
        self.assertEqual(2, int(context['NUMBER_OF_VOTES']))
