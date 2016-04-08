from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
import json

from .models import Category, Vote
from .utils import get_voter, get_number_of_votes, vote_needs_captcha, get_site_mode


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

    mode = get_site_mode()

    return {
        'CAPTCHA_SITE_KEY': settings.NORECAPTCHA_SITE_KEY,
        'DEBUG': settings.DEBUG,
        'VOTE_NEEDS_CAPTCHA': vote_needs_captcha(request),
        'NUMBER_OF_VOTES': get_number_of_votes() if mode.show_total_votes else 0,  # Just in case
        'STATIC_URL': settings.STATIC_URL,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'MIXPANEL_KEY': settings.MIXPANEL_KEY,
        'SHOW_QUESTION_VOTES': mode.show_question_votes,
        'SHOW_TOTAL_VOTES': mode.show_total_votes,
        'ALLOW_SORTING_BY_VOTES': mode.allow_sorting_by_votes,
        'ALLOW_VOTING_AND_SUBMITTING_QUESTIONS': mode.allow_voting_and_submitting_questions,
        'DEBATE_TIME': mode.debate_time,
        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories),
        'SITE_THEME_NAME': settings.SITE_THEME_NAME,
        'SITE_THEME': settings.SITE_THEMES[settings.SITE_THEME_NAME],
    }
