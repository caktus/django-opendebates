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
    debate = request.debate

    context = {
        'CAPTCHA_SITE_KEY': settings.NORECAPTCHA_SITE_KEY,
        'DEBUG': settings.DEBUG,
        'STATIC_URL': settings.STATIC_URL,
        'SUBMISSIONS_PER_PAGE': settings.SUBMISSIONS_PER_PAGE,
        'MIXPANEL_KEY': settings.MIXPANEL_KEY,
        'OPTIMIZELY_KEY': settings.OPTIMIZELY_KEY,
        'SITE_THEME_NAME': settings.SITE_THEME_NAME,
    }
    if debate is None:
        return context

    def _get_categories():
        return Category.objects.filter(debate=debate)

    site_domain_with_protocol = "%s://%s/%s" % (request.scheme, debate.site.domain, debate.prefix)
    url_tmpl = u"https://twitter.com/intent/tweet?url=%(SITE_DOMAIN)s&text=%(tweet_text)s"
    TWITTER_URL = url_tmpl % {
        "SITE_DOMAIN": quote_plus(site_domain_with_protocol + "?source=tw-site"),
        "tweet_text": quote_plus(debate.twitter_site_text),
    }
    FACEBOOK_URL = u"https://www.facebook.com/sharer/sharer.php?&u=%(url)s" % {
        "url": quote_plus(site_domain_with_protocol + "?source=fb-site"),
    }

    votes_key = NUMBER_OF_VOTES_CACHE_ENTRY.format(debate.id)

    context.update({
        'VOTE_NEEDS_CAPTCHA': vote_needs_captcha(request),
        'NUMBER_OF_VOTES': (cache.get(votes_key) or 0) if debate.show_total_votes else 0,

        'FACEBOOK_URL': FACEBOOK_URL,
        'TWITTER_URL': TWITTER_URL,

        'SITE_DOMAIN': debate.site.domain,
        'SITE_LINK': site_domain_with_protocol,
        'SHOW_QUESTION_VOTES': debate.show_question_votes,
        'SHOW_TOTAL_VOTES': debate.show_total_votes,
        'ALLOW_SORTING_BY_VOTES': debate.allow_sorting_by_votes,
        'ALLOW_VOTING_AND_SUBMITTING_QUESTIONS': debate.allow_voting_and_submitting_questions,
        'DEBATE_TIME': debate.debate_time,
        'PREVIOUS_DEBATE_TIME': (
            debate.previous_debate_time if debate.previous_debate_time and
            debate.previous_debate_time < now() else None
        ),
        'LOCAL_VOTES_STATE': debate.debate_state,
        'ANNOUNCEMENT': {
            'headline': debate.announcement_headline,
            'body': debate.announcement_body,
            'link': debate.announcement_link,
        } if (debate.announcement_headline and
              (not debate.announcement_page_regex or
               re.match(debate.announcement_page_regex, request.path))
              ) else None,

        'BANNER_HEADER_TITLE': debate.banner_header_title,
        'BANNER_HEADER_COPY': debate.banner_header_copy,
        # Note: POPUP_AFTER_SUBMISSION_TEXT is not actually json; this is used
        # to provide a string surrounded by double quotes with all the necessary
        # characters escaped. See PR #188.
        'POPUP_AFTER_SUBMISSION_TEXT': json.dumps(debate.popup_after_submission_text),

        'SUBMISSION_CATEGORIES': SimpleLazyObject(_get_categories),
        'DEBATE': debate,
    })
    return context
