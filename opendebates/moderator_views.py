from djangohelpers.lib import rendered_with, allow_http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from opendebates_emails.models import send_email
from .forms import ModerationForm, TopSubmissionForm
from .models import Submission, Vote, Flag
from .utils import get_local_votes_state


@rendered_with("opendebates/moderation/preview.html")
@allow_http("GET", "POST")
@login_required
def preview(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = ModerationForm(data=request.POST or None, initial=request.GET or None)
    if request.method == 'POST':
        if form.is_valid():
            to_remove = form.cleaned_data['to_remove_obj']
            duplicate_of = form.cleaned_data.get('duplicate_of_obj')
            post_url = 'moderation_merge' if duplicate_of else 'moderation_remove'

            return {
                'form': form,
                'to_remove': to_remove,
                'duplicate_of': duplicate_of,
                'post_url': post_url
            }
    return {'form': form}


@allow_http("POST")
@login_required
def merge(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    to_remove = get_object_or_404(Submission, pk=request.POST['to_remove'], approved=True)
    duplicate_of = get_object_or_404(Submission, pk=request.POST['duplicate_of'], approved=True)

    if request.POST.get("action").lower() == "reject":
        msg = _(u'No changes made and flag has been removed.')
    elif request.POST.get("action").lower() == "unmoderate":
        msg = _(u'Duplicate has been removed, and votes have not been merged.')
        to_remove.approved = False
        to_remove.duplicate_of = duplicate_of
        to_remove.save()
        if request.POST.get("send_email") == "yes":
            send_email("your_idea_is_duplicate", {"idea": to_remove})
    elif request.POST.get("action").lower() == "merge":
        votes_already_cast = list(Vote.objects.filter(
            submission=duplicate_of).values_list("voter_id", flat=True))
        votes_to_merge = Vote.objects.filter(submission=to_remove).exclude(
            voter__in=votes_already_cast)

        local_state = get_local_votes_state()
        if local_state:
            local_votes_to_merge = votes_to_merge.filter(voter__state=local_state).count()
        else:
            local_votes_to_merge = 0

        duplicate_of.keywords = (duplicate_of.keywords or '') \
            + " " + to_remove.idea \
            + " " + (to_remove.keywords or '')
        duplicate_of.has_duplicates = True
        duplicate_of.votes += votes_to_merge.count()
        duplicate_of.local_votes += local_votes_to_merge
        duplicate_of.save()
        votes_to_merge.update(original_merged_submission=to_remove, submission=duplicate_of)
        to_remove.duplicate_of = duplicate_of
        to_remove.save()
        msg = _(u'Question has been merged.')
        if request.POST.get("send_email") == "yes":
            send_email("your_idea_is_merged", {"idea": to_remove})
            send_email("idea_merged_into_yours", {"idea": duplicate_of})
    else:
        return HttpResponseBadRequest('Invalid value for "action".')

    # mark all flags of this merge as 'reviewed'
    Flag.objects.filter(
        to_remove=to_remove,
        duplicate_of=duplicate_of,
        reviewed=False
    ).update(reviewed=True)

    messages.info(request, msg)
    return redirect('moderation_home')


@allow_http("POST")
@login_required
def remove(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    to_remove = get_object_or_404(Submission, pk=request.POST.get('to_remove'), approved=True)

    remove = request.POST.get('action').lower() == 'remove'
    if remove:
        to_remove.approved = False
        msg = _(u'The question has been removed.')
    else:
        msg = _(u'The question has been kept and removed from the moderation list.')
    to_remove.moderated_removal = True
    to_remove.removal_flags.all().update(reviewed=True)
    to_remove.save()

    if remove and request.POST.get("send_email") == "yes":
        send_email("idea_is_removed", {"idea": to_remove})
    messages.info(request, msg)
    return redirect('moderation_home')


@rendered_with("opendebates/moderation/home.html")
@allow_http("GET")
@login_required
def home(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    # submissions:
    #   - which have removal flags without duplicate_of (so not merges)
    #   - which have not already been moderated
    #   - ordered by flag count
    flagged_for_removal = Submission.objects.filter(removal_flags__duplicate_of=None) \
                                            .exclude(moderated_removal=True) \
                                            .annotate(num_flags=Count('removal_flags')) \
                                            .filter(num_flags__gt=0) \
                                            .order_by('-num_flags')

    # all merge flags which have not yet been reviewed and whose targets have not been removed
    merge_flags = Flag.objects.exclude(duplicate_of=None) \
                              .exclude(reviewed=True) \
                              .exclude(duplicate_of__moderated_removal=True) \
                              .exclude(to_remove__moderated_removal=True)

    return {
        'flagged_for_removal': flagged_for_removal,
        'merge_flags': merge_flags,
    }


@rendered_with("opendebates/moderation/top_archive.html")
def add_to_top_archive(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    form = TopSubmissionForm(data=request.POST or None, initial=request.GET or None)
    if request.method == 'POST':
        if form.is_valid():
            entry = form.save()
            return redirect("top_archive", slug=entry.category.slug)

    return {"form": form}
