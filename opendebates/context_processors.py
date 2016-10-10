import json
import re
from urllib import quote_plus

from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
from django.utils.timezone import now

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

    url_tmpl = u"https://twitter.com/intent/tweet?url=%(SITE_DOMAIN)s&text=%(tweet_text)s"
    TWITTER_URL = url_tmpl % {
        "SITE_DOMAIN": quote_plus(settings.SITE_DOMAIN_WITH_PROTOCOL + "?source=tw-site"),
        "tweet_text": quote_plus(mode.twitter_site_text),
    }
    FACEBOOK_URL = u"https://www.facebook.com/sharer/sharer.php?&u=%(url)s" % {
        "url": quote_plus(settings.SITE_DOMAIN_WITH_PROTOCOL + "?source=fb-site"),
    }

    return {
        'CAPTCHA_SITE_KEY': settings.NORECAPTCHA_SITE_KEY,
        'DEBUG': settings.DEBUG,
        'VOTE_NEEDS_CAPTCHA': vote_needs_captcha(request),

        # FIXME: this is the number after the fraudulent votes have
        # been subtracted out.  Implement a real solution for
        # detecting and marking bad votes without deleting them outright.
        'NUMBER_OF_VOTES': 3676251,

        'STATIC_URL': settings.STATIC_URL,

        'FACEBOOK_URL': FACEBOOK_URL,
        'TWITTER_URL': TWITTER_URL,

        'SUBMISSIONS_PER_PAGE': settings.SUBMISSIONS_PER_PAGE,
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SITE_LINK': settings.SITE_DOMAIN_WITH_PROTOCOL,
        'MIXPANEL_KEY': settings.MIXPANEL_KEY,
        'OPTIMIZELY_KEY': settings.OPTIMIZELY_KEY,
        'SHOW_QUESTION_VOTES': mode.show_question_votes,
        'SHOW_TOTAL_VOTES': mode.show_total_votes,
        'ALLOW_SORTING_BY_VOTES': mode.allow_sorting_by_votes,
        'ALLOW_VOTING_AND_SUBMITTING_QUESTIONS': mode.allow_voting_and_submitting_questions,
        'DEBATE_TIME': mode.debate_time,
        'PREVIOUS_DEBATE_TIME': (
            mode.previous_debate_time if mode.previous_debate_time and
            mode.previous_debate_time < now() else None
        ),
        'LOCAL_VOTES_STATE': mode.debate_state,
        'ANNOUNCEMENT': {
            'headline': mode.announcement_headline,
            'body': mode.announcement_body,
            'link': mode.announcement_link,
        } if (mode.announcement_headline and
              (not mode.announcement_page_regex or
               re.match(mode.announcement_page_regex, request.path))
              ) else None,

        'BANNER_HEADER_TITLE': mode.banner_header_title,
        'BANNER_HEADER_COPY': mode.banner_header_copy,
        # Note: POPUP_AFTER_SUBMISSION_TEXT is not actually json; this is used
        # to provide a string surrounded by double quotes with all the necessary
        # characters escaped. See PR #188.
        'POPUP_AFTER_SUBMISSION_TEXT': json.dumps(mode.popup_after_submission_text),

        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories),
        'SITE_THEME_NAME': settings.SITE_THEME_NAME,
        'SITE_MODE': mode,
    }
