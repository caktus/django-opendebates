from __future__ import absolute_import
import logging

from celery import shared_task
from django.core.cache import cache
from django.db.models import F

from opendebates.models import Vote, Submission, RECENT_EVENTS_CACHE_ENTRY


logger = logging.getLogger(__name__)


@shared_task
def update_recent_events():
    """
    Compute recent events and cache them for the recent events view to use.
    """
    logger.debug("update_recent_events: started")

    votes = Vote.objects.select_related(
        "voter", "voter__user", "submission").exclude(
        voter=F('submission__voter')).order_by("-id")[:10]
    submissions = Submission.objects.select_related(
        "voter", "voter__user").order_by("-id")[:10]

    entries = list(votes) + list(submissions)
    entries = sorted(entries, key=lambda x: x.created_at, reverse=True)[:10]

    cache.set(RECENT_EVENTS_CACHE_ENTRY, entries, 30)

    logger.debug("There are %d entries" % len(entries))
