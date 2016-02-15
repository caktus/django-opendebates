# coding=utf-8
import logging

from django.core.mail import send_mail
from django.db import models
from django.template import Template, Context
from djangohelpers.lib import register_admin

from opendebates.models import Submission
from opendebates_emails.tasks import send_email_task

logger = logging.getLogger(__name__)


class EmailTemplate(models.Model):

    type = models.CharField(max_length=255, db_index=True)

    name = models.CharField(max_length=255)

    subject = models.CharField(max_length=500)
    html = models.TextField()
    text = models.TextField()

    from_email = models.CharField(max_length=255)
    to_email = models.CharField(max_length=255)

    def send(self, ctx):
        ctx = Context(ctx)

        subject = Template(self.subject).render(ctx)
        subject = ' '.join(subject.splitlines())

        from_email = Template(self.from_email).render(ctx)
        from_email = ' '.join(from_email.splitlines())

        to_email = Template(self.to_email).render(ctx)
        to_email = ' '.join(to_email.splitlines())

        return send_mail(subject, message=Template(self.text).render(ctx),
                         from_email=from_email, recipient_list=[to_email],
                         html_message=Template(self.html).render(ctx))


def send_email(type, ctx):
    if not EmailTemplate.objects.filter(type=type).exists():
        logger.warning("send_mail called with non-existent mail template: %r", type)
        return
    if ctx.keys() != ['idea']:
        logger.warning("send_email assumes context contains one key named 'idea'")
        return
    idea = ctx['idea']
    if not isinstance(idea, Submission):
        logger.warning("send_email assumes context['idea'] is a Submission object")
        return
    send_email_task.delay(type, idea.pk)


register_admin(EmailTemplate)

"""
Emails to be defined:

your_idea_is_merged : idea
idea_merged_into_yours : idea
idea_is_duplicate : idea
idea_is_removed : idea
submitted_new_idea : idea
"""
