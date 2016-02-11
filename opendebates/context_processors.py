from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
import json

from .forms import VoterForm
from .models import Category, Vote
from .utils import get_voter, get_number_of_votes


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

    def _get_vote_form():
        """
        We need a vote form in any template that needs to render the modal vote
        dialog, so we can properly render the captcha field. It's simpler to just
        provide it here (lazily) than to try to find all the views that would need
        to add it.
        """
        return VoterForm()

    return {
        'VOTER': SimpleLazyObject(_get_voter),
        'VOTER_FORM': SimpleLazyObject(_get_vote_form),
        'VOTES_CAST': SimpleLazyObject(_get_votes),
    }


def global_vars(request):
    def _get_categories():
        return Category.objects.all()

    return {
        'DEBUG': settings.DEBUG,
        'NUMBER_OF_VOTES': get_number_of_votes(),
        'STATIC_URL': settings.STATIC_URL,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories)
    }
