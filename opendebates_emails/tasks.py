import logging

from celery import shared_task

from opendebates.models import Submission

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(type, idea_pk):
    # Avoid circular import:
    from opendebates_emails.models import EmailTemplate

    logger.debug("send_email_task(%s, %s)", type, idea_pk)
    try:
        try:
            template = EmailTemplate.objects.filter(type=type).order_by("?")[0]
        except IndexError:
            return False

        idea = Submission.objects.get(pk=idea_pk)
        return template.send({'idea': idea})
    except Exception:
        logger.exception("Unexpected exception in send_email_task: {}")
