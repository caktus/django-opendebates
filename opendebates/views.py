from django.contrib import messages
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import connections
from django.db.models import F
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import redirect
from djangohelpers.lib import rendered_with, allow_http

import json
import logging

from registration.backends.simple.views import RegistrationView

from .forms import OpenDebatesRegistrationForm, VoterForm, QuestionForm
from .models import Submission, Voter, Vote, Category, Candidate, ZipCode, RECENT_EVENTS_CACHE_ENTRY
from .router import readonly_db
from .utils import get_ip_address_from_request, get_headers_from_request, choose_sort, sort_list
# from opendebates_comments.forms import CommentForm
from opendebates_emails.models import send_email


def health_check(request):
    """
    Health check for the load balancer.
    """
    logger = logging.getLogger('opendebates.views.health_check')
    db_errors = []
    for conn_name in connections:
        conn = connections[conn_name]
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            row = cursor.fetchone()
            assert row[0] == 1
        except Exception as e:
            # note that there doesn't seem to be a way to pass a timeout to
            # psycopg2 through Django, so this will likely not raise a timeout
            # exception
            logger.warning('Caught error checking database connection "{0}"'
                           ''.format(conn_name), exc_info=True)
            db_errors.append(e)
    if not db_errors:
        return HttpResponse('OK')
    else:
        return HttpResponseServerError('Configuration Error')


def state_from_zip(zip):
    try:
        return ZipCode.objects.get(zip=zip).state
    except ZipCode.DoesNotExist:
        return ''


@allow_http("GET")
@rendered_with("opendebates/test.html")
def test(request):
    copy = _("This is my inappropriately PCCC-specific site copy!")
    return {
        "copy": copy
    }


@allow_http("GET")
@rendered_with("opendebates/snippets/recent_activity.html")
def recent_activity(request):
    entries = cache.get(RECENT_EVENTS_CACHE_ENTRY, default=[])
    return {
        "recent_activity": entries
    }


@rendered_with("opendebates/list_ideas.html")
def list_ideas(request):
    ideas = Submission.objects.all()
    citations_only = request.GET.get("citations_only")
    sort = choose_sort(request.GET.get('sort'))

    ideas = sort_list(citations_only, sort, ideas)

    return {
        'ideas': ideas,
        'sort': sort,
        'url_name': reverse('list_ideas'),
        'stashed_submission': request.session.pop(
            "opendebates.stashed_submission", None) if request.user.is_authenticated() else None,
    }


@rendered_with("opendebates/list_ideas.html")
def list_category(request, cat_id):
    category = Category.objects.get(id=cat_id)
    ideas = Submission.objects.filter(category=cat_id)
    citations_only = request.GET.get("citations_only")
    sort = choose_sort(request.GET.get('sort'))

    ideas = sort_list(citations_only, sort, ideas)

    return {
        'ideas': ideas,
        'sort': sort,
        'url_name': reverse("list_category", kwargs={'cat_id': cat_id}),
        'category': category
    }


@rendered_with("opendebates/list_ideas.html")
@allow_http("GET")
def search_ideas(request):
    if not request.GET.get("q"):
        return redirect("/")

    ideas = Submission.objects.all()
    citations_only = request.GET.get("citations_only")
    search_term = request.GET['q']

    sort = choose_sort(request.GET.get('sort'))
    ideas = sort_list(citations_only, sort, ideas)
    ideas = ideas.search(search_term.replace("%", ""))

    return {
        'ideas': ideas,
        'search_term': search_term,
        'sort': sort,
        'url_name': reverse('search_ideas'),
    }


@rendered_with("opendebates/list_ideas.html")
def category_search(request, cat_id):
    ideas = Submission.objects.filter(category=cat_id)
    citations_only = request.GET.get("citations_only")
    search_term = request.GET['q']

    sort = choose_sort(request.GET.get('sort'))

    ideas = sort_list(citations_only, sort, ideas)
    ideas = ideas.search(search_term.replace("%", ""))

    return {
        'ideas': ideas,
        'search_term': search_term,
        'sort': sort,
        'url_name': reverse("list_category", kwargs={'cat_id': cat_id})
    }


@rendered_with("opendebates/vote.html")
@allow_http("GET", "POST")
def vote(request, id):
    try:
        with readonly_db():
            idea = Submission.objects.get(id=id, approved=True)
    except Submission.DoesNotExist:
        raise Http404

    if idea.duplicate_of_id:
        url = reverse("show_idea", kwargs={"id": idea.duplicate_of_id})
        url = url + "#i"+str(idea.id)
        return redirect(url)

    if request.method == "GET":
        two_other_approved_ideas = list(Submission.objects.filter(
            category=idea.category,
            duplicate_of=None,
            approved=True).exclude(id=idea.id)[:2]) + [None, None]
        related1 = two_other_approved_ideas[0]
        related2 = two_other_approved_ideas[1]
        return {
            'idea': idea,
            'show_duplicates': True,
            'related1': related1,
            'related2': related2,
            'duplicates': (Submission.objects.filter(approved=True, duplicate_of=idea)
                           if idea.has_duplicates else []),
            # 'comment_form': CommentForm(idea),
            # 'comment_list': idea.comments.filter(
            #     is_public=True, is_removed=False
            # ).select_related("user", "user__voter"),
        }

    form = VoterForm(request.POST)
    if not form.is_valid():
        if request.is_ajax():
            return HttpResponse(
                json.dumps({"status": "400", "errors": form.errors}),
                content_type="application/json")
        messages.error(request, _('You have some errors in your form'))
        return {
            'form': form,
            'idea': idea,
            # 'comment_form': CommentForm(idea),
            }

    state = state_from_zip(form.cleaned_data['zipcode'])

    voter, created = Voter.objects.get_or_create(
        email=form.cleaned_data['email'],
        defaults=dict(
            source=request.COOKIES.get('opendebates.source'),
            state=state,
            zip=form.cleaned_data['zipcode'],
        )
    )

    if voter.user and voter.user != request.user:
        # anonymous user can't use the email of a registered user
        msg = 'That email is registered. Please login and try again.'
        if request.is_ajax():
            return HttpResponse(
                json.dumps({"status": "400", "errors": {'email': msg}}),
                content_type="application/json")
        messages.error(request, _(msg))
        return {
            'form': form,
            'idea': idea,
            # 'comment_form': CommentForm(idea),
        }

    if not created and voter.zip != form.cleaned_data['zipcode']:
        voter.zip = form.cleaned_data['zipcode']
        voter.state = state
        voter.save()

    vote, created = Vote.objects.get_or_create(
        submission=idea,
        voter=voter,
        defaults=dict(
            ip_address=get_ip_address_from_request(request),
            created_at=timezone.now(),
            source=request.COOKIES.get('opendebates.source'),
            request_headers=get_headers_from_request(request),

        )
    )
    if created:
        # update the DB with the real tally
        Submission.objects.filter(id=id).update(votes=F('votes')+1)
        # also calculate a simple increment tally for the client
        idea.votes += 1

    if 'voter' not in request.session:
        request.session['voter'] = {"email": voter.email, "zip": voter.zip}

    if request.is_ajax():
        return HttpResponse(
            json.dumps({"status": "200", "tally": idea.votes, "id": idea.id}),
            content_type="application/json")

    url = reverse("vote", kwargs={'id': id})
    return redirect(url)


@rendered_with("opendebates/list_ideas.html")
@allow_http("GET", "POST")
def questions(request):

    if request.method == 'GET':
        form = QuestionForm()

        return {
            'form': form,
            'categories': Category.objects.all(),
            'ideas': [],
            'stashed_submission': request.session.pop(
                "opendebates.stashed_submission", None)
            if request.user.is_authenticated() else None,
        }

    form = QuestionForm(request.POST)

    if not form.is_valid():
        # form = QuestionForm()
        messages.error(request, _('You have some errors in the form'))

        return {
            'form': form,
            'categories': Category.objects.all(),
            'ideas': [],
        }

    if not request.user.is_authenticated():
        request.session['opendebates.stashed_submission'] = {
            "category": request.POST['category'],
            "question": request.POST['question'],
            "citation": request.POST.get("citation"),
        }
        return redirect("registration_register")

    category = request.POST.get('category')
    form_data = form.cleaned_data

    voter, created = Voter.objects.get_or_create(
        email=request.user.email,
        defaults=dict(
            source=request.COOKIES.get('opendebates.source')
        )
    )

    idea = Submission.objects.create(
        voter=voter,
        category_id=category,
        headline=form_data['headline'],
        idea=form_data['question'],
        citation=form_data['citation'],
        created_at=timezone.now(),
        ip_address=get_ip_address_from_request(request),
        approved=True,
        votes=1,
        source=request.COOKIES.get('opendebates.source'),
    )

    Vote.objects.create(
        submission=idea,
        voter=voter,
        source=idea.source,
        ip_address=get_ip_address_from_request(request),
        request_headers=get_headers_from_request(request),
        created_at=timezone.now())

    send_email("submitted_new_idea", {"idea": idea})

    url = reverse("vote", kwargs={'id': idea.id})
    return redirect(url)


class OpenDebatesRegistrationView(RegistrationView):

    form_class = OpenDebatesRegistrationForm

    def register(self, request, form):
        new_user = RegistrationView.register(self, request, form)
        new_user.first_name = form.cleaned_data['first_name']
        new_user.last_name = form.cleaned_data['last_name']
        new_user.save()

        try:
            voter = Voter.objects.get(email=form.cleaned_data['email'])
        except Voter.DoesNotExist:
            voter = Voter(email=form.cleaned_data['email'])
            if 'opendebates.source' in request.COOKIES:
                voter.source = request.COOKIES['opendebates.source']

        voter.zip = form.cleaned_data['zip']
        try:
            voter.state = ZipCode.objects.get(zip=form.cleaned_data['zip']).state
        except Exception:
            pass
        voter.display_name = form.cleaned_data.get('display_name')
        voter.twitter_handle = form.cleaned_data.get('twitter_handle')
        voter.user = new_user
        voter.save()

        return new_user


def registration_complete(request):
    request.session['events.account_created'] = True
    return redirect("/")


@rendered_with("opendebates/list_candidates.html")
@allow_http("GET")
def list_candidates(request):
    candidates = Candidate.objects.order_by('last_name', 'first_name')
    return {
        'candidates': candidates,
    }
