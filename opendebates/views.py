import json
import logging

from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import connections
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.http import Http404, HttpResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from djangohelpers.lib import rendered_with, allow_http
from registration.backends.simple.views import RegistrationView

from .forms import OpenDebatesRegistrationForm, VoterForm, QuestionForm, MergeFlagForm
from .models import (Candidate, Category, Flag, Submission, Vote, Voter,
                     TopSubmissionCategory, ZipCode, RECENT_EVENTS_CACHE_ENTRY)
from .router import readonly_db
from .utils import (get_ip_address_from_request, get_headers_from_request, choose_sort, sort_list,
                    vote_needs_captcha, registration_needs_captcha, get_voter)
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


@cache_page(5)  # Cache for 5 seconds after rendering
@allow_http("GET")
@rendered_with("opendebates/snippets/recent_activity.html")
def recent_activity(request):
    entries = cache.get(RECENT_EVENTS_CACHE_ENTRY.format(request.debate.id), default=[])
    return {
        "recent_activity": entries
    }


@rendered_with("opendebates/list_ideas.html")
def list_ideas(request):
    ideas = Submission.objects.filter(category__debate=request.debate)
    citations_only = request.GET.get("citations_only")
    sort = choose_sort(request, request.GET.get('sort'))

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
    category = get_object_or_404(Category, id=cat_id, debate=request.debate)
    ideas = Submission.objects.filter(category__debate=request.debate, category=cat_id)
    citations_only = request.GET.get("citations_only")
    sort = choose_sort(request, request.GET.get('sort'))

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
    try:
        search_term = [q for q in request.GET.getlist("q") if q][0]
    except IndexError:
        return redirect(reverse('list_ideas'))

    ideas = Submission.objects.filter(category__debate=request.debate)
    citations_only = request.GET.get("citations_only")

    sort = choose_sort(request, request.GET.get('sort'))
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
    ideas = Submission.objects.filter(category__debate=request.debate, category=cat_id)
    citations_only = request.GET.get("citations_only")
    search_term = request.GET['q']

    sort = choose_sort(request, request.GET.get('sort'))

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
    """Despite the name, this is both the page for voting AND the detail page for submissions"""
    try:
        with readonly_db():
            idea = Submission.objects.get(
                id=id, category__debate=request.debate,
            )
    except Submission.DoesNotExist:
        raise Http404
    if request.method == "POST" and not idea.approved:
        # Don't allow voting on removed submissions, but do allow viewing them
        raise Http404

    if idea.duplicate_of_id:
        if not idea.approved:
            # Submissions which have been "unmoderated as duplicates"
            # should remain completely inaccessible, and should not redirect
            raise Http404
        url = reverse("show_idea", kwargs={'id': idea.duplicate_of_id})
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
            'duplicates': (Submission.objects.filter(
                                category__debate=request.debate,
                                approved=True, duplicate_of=idea)
                           if idea.has_duplicates else []),
        }

    if not request.debate.allow_voting_and_submitting_questions:
        raise Http404

    form = VoterForm(request.POST)
    if not vote_needs_captcha(request):
        form.ignore_captcha()
    if not form.is_valid():
        if request.is_ajax():
            return HttpResponse(
                json.dumps({"status": "400", "errors": form.errors}),
                content_type="application/json")
        messages.error(request, _('You have some errors in your form'))
        return {
            'form': form,
            'idea': idea,
        }
    state = state_from_zip(form.cleaned_data['zipcode'])

    is_fraudulent = False

    session_key = request.session.session_key or ''
    if session_key and Vote.objects.filter(submission=idea,
                                           sessionid=session_key).exists():
        # Django creates a session for both signed-in users and anonymous, so
        # we should be able to rely on this.  If it is duplicated on a given
        # question, it's because they are scripting votes.  Behave the same
        # way as if it was a normal email duplicate, i.e. don't increment but
        # return without error.
        is_fraudulent = True

    session_voter = get_voter(request)
    if session_voter and session_voter['email'] != form.cleaned_data['email']:
        # This can only happen with an manually-created POST request.
        is_fraudulent = True

    if is_fraudulent:
        # Pretend like everything is fine, but don't increment the tally or
        # create a Vote.  Deny attackers any information about how they are failing.
        if request.is_ajax():
            result = {"status": "200",
                      "tally": idea.votes if request.debate.show_question_votes else '',
                      "id": idea.id}
            return HttpResponse(
                json.dumps(result),
                content_type="application/json")

        url = reverse("vote", kwargs={'id': id})
        return redirect(url)

    voter, created = Voter.objects.get_or_create(
        email=form.cleaned_data['email'],
        defaults=dict(
            source=request.COOKIES.get('opendebates.source'),
            state=state,
            zip=form.cleaned_data['zipcode'],
            user=request.user if request.user.is_authenticated() else None,
        )
    )

    if not created and voter.zip != form.cleaned_data['zipcode']:
        voter.zip = form.cleaned_data['zipcode']
        voter.state = state
        voter.save()

    vote, created = Vote.objects.get_or_create(
        submission=idea,
        voter=voter,
        defaults=dict(
            created_at=timezone.now(),
            source=request.COOKIES.get('opendebates.source'),
            ip_address=get_ip_address_from_request(request),
            sessionid=session_key,
            request_headers=get_headers_from_request(request),
            is_suspicious=False,
            is_invalid=False,
        )
    )

    previous_debate_time = request.debate.previous_debate_time
    if created:
        # update the DB with the real tally
        Submission.objects.filter(category__debate=request.debate, id=id).update(
            votes=F('votes')+1,
            current_votes=F('current_votes')+(
                1 if previous_debate_time is None or vote.created_at > previous_debate_time
                else 0
            ),
            local_votes=F('local_votes')+(
                1 if voter.state and voter.state == request.debate.debate_state
                else 0)
        )
        # also calculate a simple increment tally for the client
        idea.votes += 1

    if 'voter' not in request.session:
        request.session['voter'] = {"email": voter.email, "zip": voter.zip}

    if request.is_ajax():
        result = {"status": "200",
                  "tally": idea.votes if request.debate.show_question_votes else '',
                  "id": idea.id}
        return HttpResponse(
            json.dumps(result),
            content_type="application/json")

    url = reverse("vote", kwargs={'id': id})
    return redirect(url)


@rendered_with("opendebates/list_ideas.html")
@allow_http("GET", "POST")
def questions(request):

    if request.method == 'GET':
        return redirect("/")

    if not request.debate.allow_voting_and_submitting_questions:
        raise Http404

    form = QuestionForm(request.POST, request=request)

    if not form.is_valid():
        # form = QuestionForm(request=request)
        messages.error(request, _('You have some errors in the form'))

        return {
            'form': form,
            'categories': Category.objects.filter(debate=request.debate),
            'ideas': [],
        }

    if not request.user.is_authenticated():
        request.session['opendebates.stashed_submission'] = {
            "category": request.POST['category'],
            "headline": request.POST['headline'],
            "question": request.POST['question'],
            "citation": request.POST.get("citation"),
        }
        return redirect('registration_register')

    category = request.POST.get('category')
    form_data = form.cleaned_data

    voter, created = Voter.objects.get_or_create(
        email=request.user.email,
        defaults=dict(
            source=request.COOKIES.get('opendebates.source')
        )
    )

    previous_debate_time = request.debate.previous_debate_time
    created_at = timezone.now()
    idea = Submission.objects.create(
        voter=voter,
        category_id=category,
        headline=form_data['headline'],
        followup=form_data['question'],
        idea=(u'%s %s' % (form_data['headline'], form_data['question'])).strip(),
        citation=form_data['citation'],
        created_at=created_at,
        ip_address=get_ip_address_from_request(request),
        approved=True,
        votes=1,
        local_votes=1 if voter.state and voter.state == request.debate.debate_state else 0,
        current_votes=(1 if previous_debate_time is None or created_at > previous_debate_time
                       else 0),
        source=request.COOKIES.get('opendebates.source'),
    )

    Vote.objects.create(
        submission=idea,
        voter=voter,
        source=idea.source,
        ip_address=get_ip_address_from_request(request),
        sessionid=request.session.session_key or '',
        request_headers=get_headers_from_request(request),
        created_at=created_at,
        is_suspicious=False,
        is_invalid=False,
    )

    send_email("submitted_new_idea", {"idea": idea})
    send_email("notify_moderators_submitted_new_idea", {"idea": idea})

    url = reverse("vote", kwargs={'id': idea.id})
    return redirect(url + "#created=%s" % idea.id)


@rendered_with("opendebates/changelog.html")
def changelog(request):
    moderated = Submission.objects.filter(
        Q(approved=False) | Q(duplicate_of__isnull=False)
    ).select_related('duplicate_of').order_by('-moderated_at', '-id')
    return {
        'moderated': moderated
    }


class OpenDebatesRegistrationView(RegistrationView):

    form_class = OpenDebatesRegistrationForm
    next = None
    prefix = None

    def get(self, request):
        self.next = request.GET.get('next', None)
        return super(OpenDebatesRegistrationView, self).get(request)

    def get_context_data(self, *args, **kwargs):
        data = super(OpenDebatesRegistrationView, self).get_context_data(*args, **kwargs)
        if self.next:
            data['next'] = self.next
        return data

    def form_valid(self, request, form):
        User = get_user_model()
        if User.objects.filter(email__iexact=form.cleaned_data['email']).exists():
            return redirect(reverse('registration_duplicate'))
        return super(OpenDebatesRegistrationView, self).form_valid(request, form)

    def register(self, request, form):
        new_user = super(OpenDebatesRegistrationView, self).register(request, form)

        voter, created = Voter.objects.update_or_create(
            email=form.cleaned_data['email'],
            defaults=dict(
                source=request.COOKIES.get('opendebates.source'),
                state=state_from_zip(form.cleaned_data['zip']),
                zip=form.cleaned_data['zip'],
                display_name=form.cleaned_data.get('display_name'),
                twitter_handle=form.cleaned_data.get('twitter_handle'),
                phone_number=form.cleaned_data.get('phone_number'),
                user=new_user,
            )
        )
        return new_user

    def get_form_kwargs(self):
        kwargs = super(OpenDebatesRegistrationView, self).get_form_kwargs()
        kwargs.update({
            'request': self.request,
        })
        return kwargs

    def get_form(self, form_class=None):
        form = super(OpenDebatesRegistrationView, self).get_form(form_class)
        if not registration_needs_captcha(self.request):
            form.ignore_captcha()
        return form

    def get_success_url(self, request, user):
        if request.GET.get('next'):
            return request.GET.get('next')
        else:
            return reverse('registration_complete')


def registration_complete(request):
    request.session['events.account_created'] = True
    return redirect(reverse('list_ideas'))


@rendered_with("registration/registration_duplicate.html")
def registration_duplicate(request):
    return {}


@rendered_with("opendebates/list_candidates.html")
@allow_http("GET")
def list_candidates(request):
    candidates = Candidate.objects.filter(
        debate=request.debate,
    ).order_by('last_name', 'first_name')
    return {
        'candidates': candidates,
    }


@rendered_with("opendebates/flag_report.html")
@allow_http("GET", "POST")
@login_required
def report(request, id):
    if not request.debate.allow_voting_and_submitting_questions and not request.user.is_staff:
        raise Http404

    idea = get_object_or_404(Submission, pk=id, category__debate=request.debate)
    voter = Voter.objects.get(user=request.user)

    if request.method == 'POST':
        flag, created = Flag.objects.get_or_create(
            to_remove=idea,
            voter=voter,
            duplicate_of=None,
            defaults=dict(note=request.POST.get("report_why"))
        )
        messages.info(request, _(u'This question has been flagged for removal.'))
        return redirect(idea)
    return {
        'idea': idea,
    }


@rendered_with("opendebates/flag_merge.html")
@allow_http("GET", "POST")
@login_required
def merge(request, id):
    if not request.debate.allow_voting_and_submitting_questions and not request.user.is_staff:
        raise Http404

    idea = get_object_or_404(Submission, pk=id, category__debate=request.debate)
    voter = Voter.objects.get(user=request.user)

    if Flag.objects.filter(to_remove=idea, voter=voter).exists():
        messages.info(request, _(u'You have already flagged this question.'))
        return redirect(idea)

    form = MergeFlagForm(idea=idea, voter=voter, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.info(request, _(u'This question has been flagged for merging.'))
        return redirect(idea)
    return {
        'idea': idea,
        'form': form,
    }


@rendered_with("opendebates/top_archive.html")
@allow_http("GET")
def top_archive(request, slug):
    category = get_object_or_404(TopSubmissionCategory,
                                 debate=request.debate, slug=slug)
    submissions = category.submissions.select_related(
        "submission", "submission__voter", "submission__voter__user",
        "submission__category").order_by("rank", "created_at").all()
    return {
        'category': category,
        'submissions': submissions,
    }


def od_logout(request, next_page=None,
              template_name='registration/logged_out.html',
              redirect_field_name=REDIRECT_FIELD_NAME,
              current_app=None, extra_context=None):
    if next_page is not None:
        next_page = reverse(next_page)
    return logout(request, next_page, template_name, redirect_field_name,
                  current_app, extra_context)
