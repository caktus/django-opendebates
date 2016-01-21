from djangohelpers.lib import rendered_with, allow_http
from django.http import HttpResponse
from django.shortcuts import redirect

from .models import Submission, Vote


@rendered_with("opendebates/moderation/mark_duplicate.html")
@allow_http("GET", "POST")
def mark_duplicate(request):
    if not request.user.is_superuser:
        return HttpResponse("forbidden")  # @@TODO

    to_remove_default = ''
    if request.method == "GET":
        return {'to_remove_default': request.GET.get("to_remove", "")}

    to_remove = Submission.objects.select_related("voter", "voter__user").get(
        id=request.POST['to_remove'])
    try:
        duplicate_of = Submission.objects.select_related(
            "voter", "voter__user").get(id=request.POST['duplicate_of'])
    except (KeyError, ValueError, Submission.DoesNotExist):
        duplicate_of = None

    if request.POST.get("confirm") != "confirm":
        return locals()

    if request.POST.get("handling") == "unmoderate":
        to_remove.moderated = False
    elif request.POST.get("handling") == "merge":
        duplicate_of.keywords = (duplicate_of.keywords or '') + " " + to_remove.idea
        duplicate_of.has_duplicates = True
        duplicate_of.save()
    if duplicate_of is not None:
        to_remove.duplicate_of = duplicate_of
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
        # FIXME: `emails` was not defined, so I have commented it out for now. --vkurup
        if request.POST.get("handling") == "merge":
            pass
            # emails.idea_is_merged(to_remove)
        else:
            if duplicate_of is not None:
                pass
                # emails.idea_is_duplicate(to_remove)
            else:
                pass
                # emails.idea_is_removed(to_remove)
    return redirect(".")
