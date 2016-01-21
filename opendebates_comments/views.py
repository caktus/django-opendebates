from django import http
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from opendebates_comments.forms import CommentForm
from opendebates_comments import signals
from opendebates_comments.view_utils import next_redirect, confirmation_view
from opendebates.utils import get_ip_address_from_request
from opendebates.models import Submission


class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """
    def __init__(self, why):
        super(CommentPostBadRequest, self).__init__()
        if settings.DEBUG:
            self.content = render_to_string("comments/400-debug.html", {"why": why})


@csrf_protect
@require_POST
def post_comment(request, next=None, using=None, extra_ctx={}):
    """
    Post a comment.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """
    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    if not request.user.is_authenticated():
        return redirect(settings.LOGIN_URL)

    data["name"] = request.user.get_full_name() or request.user.get_username()
    data["email"] = request.user.email

    object_id = data.get("object_id")
    if object_id is None:
        return CommentPostBadRequest("Missing object_id field.")
    # FIXME: ctype and object_pk were not defined, so I have given them dummy
    #        values for now -- vkurup
    ctype = object_pk = 'dummy value'
    try:
        target = Submission.objects.filter(approved=True, duplicate_of__isnull=True).get(
            id=object_id)
    except TypeError:
        return CommentPostBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest(
            "The given content-type %r does not resolve to a valid model." %
            escape(ctype))
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No object matching content-type %r and object PK %r exists." %
            (escape(ctype), escape(object_pk)))
    except (ValueError, ValidationError) as e:
        return CommentPostBadRequest(
            "Attempting to get content-type %r and object PK %r exists raised %s" %
            (escape(ctype), escape(object_pk), e.__class__.__name__))

    # Do we want to preview the comment?
    preview = "preview" in data

    # Construct the comment form
    form = CommentForm(target, data=data)

    # Check security information
    if form.security_errors():
        return CommentPostBadRequest(
            "The comment form failed security verification: %s" %
            escape(str(form.security_errors())))

    # If there are errors or if we requested a preview show the comment
    if form.errors or preview:
        template_list = ['opendebates/vote.html', 'opendebates/show_idea.html']

        ctx = {"comment": form.data.get("comment", ""),
               "comment_form": form,
               "next": data.get("next", next),
               "idea": target,
               }
        ctx.update(extra_ctx)

        return render_to_response(
            template_list, ctx,
            RequestContext(request, {})
        )

    # Otherwise create the comment
    comment = form.get_comment_object()

    comment.ip_address = get_ip_address_from_request(request)
    assert request.user.is_authenticated()
    comment.user = request.user

    # Signal that the comment is about to be saved
    responses = signals.comment_will_be_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    for (receiver, response) in responses:
        if response is False:
            return CommentPostBadRequest(
                "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)

    # Save the comment and signal that it was saved
    comment.save()
    signals.comment_was_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    return next_redirect(request, fallback=next or 'comments-comment-done',
                         c=comment._get_pk_val())

comment_done = confirmation_view(
    template="comments/posted.html",
    doc="""Display a "comment was posted" success page."""
)
