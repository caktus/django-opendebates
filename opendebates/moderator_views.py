from djangohelpers.lib import rendered_with, allow_http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from opendebates_emails.models import send_email
from .models import Submission, Vote, Flag


@rendered_with("opendebates/moderation/mark_duplicate.html")
@allow_http("GET", "POST")
@login_required
def mark_duplicate(request):
    if not request.user.is_superuser:
        return HttpResponseNotFound()

    to_remove_default = ''
    if request.method == "GET":
        return {'to_remove_default': request.GET.get("to_remove", "")}

    to_remove = get_object_or_404(Submission, pk=request.POST['to_remove'])
    try:
        duplicate_of = Submission.objects.get(id=request.POST['duplicate_of'])
    except (KeyError, ValueError, Submission.DoesNotExist):
        duplicate_of = None

    if request.POST.get("confirm") != "confirm":
        return locals()

    if request.POST.get("handling") == "reject_merge":
        # mark all flags of this merge as 'reviewed'
        Flag.objects.filter(to_remove=to_remove, duplicate_of=duplicate_of).update(reviewed=True)
        msg = _(u'No changes made and flag has been removed.')
    elif request.POST.get("handling") == "merge":
        duplicate_of.keywords = (duplicate_of.keywords or '') \
                                + " " + to_remove.idea \
                                + " " + (to_remove.keywords or '')
        duplicate_of.has_duplicates = True
        duplicate_of.save()
        msg = _(u'Question has been merged.')

    if duplicate_of is not None and request.POST.get('handling') == 'merge':
        # merge and mark all flags of this merge as 'reviewed'
        to_remove.duplicate_of = duplicate_of
        Flag.objects.filter(to_remove=to_remove, duplicate_of=duplicate_of).update(reviewed=True)
    else:
        msg = _(u'Question has been removed.')
        # remove and mark submission 'moderated'
        to_remove.approved = False
        to_remove.moderated_removal = True
    to_remove.save()

    if request.POST.get("handling") == "merge":
        votes_already_cast = list(Vote.objects.filter(
            submission=duplicate_of).values_list("voter_id", flat=True))
        votes_to_merge = Vote.objects.filter(submission=to_remove).exclude(
            voter__in=votes_already_cast)
        duplicate_of.votes += votes_to_merge.count()
        duplicate_of.save()
        votes_to_merge.update(original_merged_submission=to_remove, submission=duplicate_of)

    if request.POST.get("send_email") == "yes":
        if request.POST.get("handling") == "merge":
            send_email("your_idea_is_merged", {"idea": to_remove})
            send_email("idea_merged_into_yours", {"idea": duplicate_of})
        else:
            if duplicate_of is not None:
                send_email("idea_is_duplicate", {"idea": to_remove})
            else:
                send_email("idea_is_removed", {"idea": to_remove})
    messages.info(request, msg)
    return redirect('moderation_home')


@rendered_with("opendebates/moderation/remove.html")
@allow_http("POST")
@login_required
def remove(request, id):
    if not request.user.is_superuser:
        return HttpResponseNotFound()

    to_remove = get_object_or_404(Submission, pk=id)

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
        return HttpResponseNotFound()

    # submissions:
    #   - which have removal flags without duplicate_of (so not merges)
    #   - which have not already been moderated
    #   - ordered by flag count
    flagged_for_removal = Submission.objects.filter(removal_flags__duplicate_of=None) \
                                            .exclude(moderated_removal=True) \
                                            .annotate(num_flags=Count('removal_flags')) \
                                            .filter(num_flags__gt=0) \
                                            .order_by('-num_flags')

    # all merge flags which have not yet been reviewed
    merge_flags = Flag.objects.exclude(duplicate_of=None).exclude(reviewed=True)

    return {
        'flagged_for_removal': flagged_for_removal,
        'merge_flags': merge_flags,
    }
