from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
import json
from .models import Category, Vote
from .utils import get_voter


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
        'DEBUG': settings.DEBUG,
        'STATIC_URL': settings.STATIC_URL,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories)
    }
