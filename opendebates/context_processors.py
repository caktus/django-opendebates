import json
import re
from urllib import quote_plus

from django.conf import settings
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.utils.html import mark_safe
from django.utils.timezone import now

from .models import Category, Vote, NUMBER_OF_VOTES_CACHE_ENTRY
from .utils import get_voter, vote_needs_captcha


def voter(request):
    def _get_voter():
        return get_voter(request)

    def _get_votes():
        voter = get_voter(request)
        if not voter:
            return '{}'
        votes = Vote.objects.filter(
            voter__email=voter['email'],
        )
        votes = [i.submission_id for i in votes]
        return mark_safe(json.dumps({"submissions": votes}))

    return {
        'VOTER': SimpleLazyObject(_get_voter),
        'VOTES_CAST': SimpleLazyObject(_get_votes),
    }


def global_vars(request):
    mode = request.site_mode

    context = {
        'CAPTCHA_SITE_KEY': settings.NORECAPTCHA_SITE_KEY,
        'DEBUG': settings.DEBUG,
        'STATIC_URL': settings.STATIC_URL,
        'SUBMISSIONS_PER_PAGE': settings.SUBMISSIONS_PER_PAGE,
        'MIXPANEL_KEY': settings.MIXPANEL_KEY,
        'OPTIMIZELY_KEY': settings.OPTIMIZELY_KEY,
        'SITE_THEME_NAME': settings.SITE_THEME_NAME,
    }
    if mode is None:
        return context

    def _get_categories():
        return Category.objects.filter(site_mode=mode)

    site_domain_with_protocol = "%s://%s/%s" % (request.scheme, mode.site.domain, mode.prefix)
    url_tmpl = u"https://twitter.com/intent/tweet?url=%(SITE_DOMAIN)s&text=%(tweet_text)s"
    TWITTER_URL = url_tmpl % {
        "SITE_DOMAIN": quote_plus(site_domain_with_protocol + "?source=tw-site"),
        "tweet_text": quote_plus(mode.twitter_site_text),
    }
    FACEBOOK_URL = u"https://www.facebook.com/sharer/sharer.php?&u=%(url)s" % {
        "url": quote_plus(site_domain_with_protocol + "?source=fb-site"),
    }

    votes_key = NUMBER_OF_VOTES_CACHE_ENTRY.format(mode.id)

    context.update({
        'VOTE_NEEDS_CAPTCHA': vote_needs_captcha(request),
        'NUMBER_OF_VOTES': (cache.get(votes_key) or 0) if mode.show_total_votes else 0,

        'FACEBOOK_URL': FACEBOOK_URL,
        'TWITTER_URL': TWITTER_URL,

        'SITE_DOMAIN': mode.site.domain,
        'SITE_LINK': site_domain_with_protocol,
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
        'SITE_MODE': mode,
    })
    return context
