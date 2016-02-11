from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
import json

from .models import Category, Vote
from .utils import get_voter, get_number_of_votes, vote_needs_captcha


def voter(request):
    def _get_voter():
        return get_voter(request)

    def _get_votes():
        voter = get_voter(request)
        if not voter:
            return '{}'
        votes = Vote.objects.filter(voter__email=voter['email'])
        votes = [i.submission_id for i in votes]
        return mark_safe(json.dumps({"submissions": votes}))

    return {
        'VOTER': SimpleLazyObject(_get_voter),
        'VOTES_CAST': SimpleLazyObject(_get_votes),
    }


def global_vars(request):
    def _get_categories():
        return Category.objects.all()

    return {
        'CAPTCHA_SITE_KEY': settings.NORECAPTCHA_SITE_KEY,
        'DEBUG': settings.DEBUG,
        'VOTE_NEEDS_CAPTCHA': vote_needs_captcha(request),
        'NUMBER_OF_VOTES': get_number_of_votes(),
        'STATIC_URL': settings.STATIC_URL,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories)
    }
