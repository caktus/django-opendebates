import json
import random
from .models import Voter


def get_voter(request):
    if request.user.is_authenticated():

        try:
            voter = request.user.voter
        except Voter.DoesNotExist:
            return {}

        return {
            'email': request.user.email,
            'zip': voter.zip,
        }
    elif 'voter' in request.session:
        return request.session['voter']


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


def choose_sort(sort):
    sort = sort or random.choice(["trending", "trending", "random"])
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

    return ideas
