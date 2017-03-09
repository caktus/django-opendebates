import json
import random

from django.conf import settings
from django.core.cache import cache
from django.contrib.sites.models import Site

from .models import Vote, Voter, NUMBER_OF_VOTES_CACHE_ENTRY, SiteMode
from .router import readwrite_db


def vote_needs_captcha(request):
    if not settings.USE_CAPTCHA:
        return False
    if not hasattr(request, 'vote_needs_captcha'):
        if request.user.is_authenticated():
            # A logged-in user has already filled out the captcha on registration
            need = False
        else:
            voter = get_voter(request)
            if voter:
                # A user's first vote requires a captcha
                need = not Vote.objects.filter(
                    voter__site_mode=request.site_mode,
                    voter__email=voter['email'],
                ).exists()
            else:
                need = True
        request.vote_needs_captcha = need
    return request.vote_needs_captcha


def registration_needs_captcha(request):
    return settings.USE_CAPTCHA


def get_number_of_votes(request):
    cache_key = '%s-%d' % (NUMBER_OF_VOTES_CACHE_ENTRY, request.site_mode.pk)
    number = cache.get(cache_key)
    return number or 0


def get_voter(request):
    if request.user.is_authenticated():
        try:
            voter = request.user.voter
        except Voter.DoesNotExist:
            # This should not happen, but it's possible if we create a user
            # somehow other than through the registration form.
            return {}

        voter = {
            'email': request.user.email,
            'zip': voter.zip,
        }
        if 'voter' not in request.session:
            request.session['voter'] = voter
        return voter
    elif 'voter' in request.session:
        return request.session['voter']
    # If we fall through make sure we have something that won't cause an error
    return {}


def get_headers_from_request(request):
    try:
        headers = {}
        for key in request.META:
            if key.startswith("HTTP_"):
                headers[key] = request.META[key]
        return json.dumps(headers)
    except Exception:
        return None


def get_ip_address_from_request(request):
    PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')
    ip_address = ''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for and ',' not in x_forwarded_for:
        if not x_forwarded_for.startswith(PRIVATE_IPS_PREFIX):
            ip_address = x_forwarded_for.strip()
    else:
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]
        for ip in ips:
            if ip.startswith(PRIVATE_IPS_PREFIX):
                continue
            else:
                ip_address = ip
                break
    if not ip_address:
        x_real_ip = request.META.get('HTTP_X_REAL_IP', '')
        if x_real_ip:
            if not x_real_ip.startswith(PRIVATE_IPS_PREFIX):
                ip_address = x_real_ip.strip()
    if not ip_address:
        remote_addr = request.META.get('REMOTE_ADDR', '')
        if remote_addr:
            if not remote_addr.startswith(PRIVATE_IPS_PREFIX):
                ip_address = remote_addr.strip()
            if remote_addr.startswith(PRIVATE_IPS_PREFIX):
                ip_address = remote_addr.strip()
    if not ip_address:
            ip_address = '127.0.0.1'
    return ip_address


def choose_sort(request, sort):
    sort = sort or random.choice(["trending", "trending", "random"])
    if sort.endswith('votes') and not request.site_mode.allow_sorting_by_votes:
        sort = 'trending'
    return sort


def sort_list(citations_only, sort, ideas):
    ideas = ideas.filter(
        approved=True,
        duplicate_of__isnull=True
    ).select_related("voter", "category", "voter__user")

    if citations_only:
        ideas = ideas.filter(citation_verified=True)

    if sort == "editors":
        ideas = ideas.order_by("-editors_pick")
    elif sort == "trending":
        ideas = ideas.order_by("-score")
    elif sort == "random":
        ideas = ideas.order_by("-random_id")
    elif sort == "-date":
        ideas = ideas.order_by("-created_at")
    elif sort == "+date":
        ideas = ideas.order_by("created_at")
    elif sort == "-votes":
        ideas = ideas.order_by("-votes")
    elif sort == "+votes":
        ideas = ideas.order_by("votes")
    elif sort == "-local_votes":
        ideas = ideas.order_by("-local_votes")
    elif sort == "-current_votes":
        ideas = ideas.order_by("-current_votes")

    return ideas


def get_site_mode(request):
    domain = request.get_host().lower().strip('.')
    try:
        return SiteMode.objects.select_related('site').get(site__domain__exact=domain)
    except SiteMode.DoesNotExist:
        with readwrite_db():
            site = Site.objects.get_or_create(domain=domain)[0]
            return SiteMode.objects.select_related('site').get_or_create(site=site)[0]
