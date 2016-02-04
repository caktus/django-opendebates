from __future__ import absolute_import
import logging

from celery import shared_task
from django.core.cache import cache
from django.db.models import F

from opendebates.models import Vote, Submission, RECENT_EVENTS_CACHE_ENTRY, \
    NUMBER_OF_VOTES_CACHE_ENTRY
from opendebates.router import set_thread_readonly_db, set_thread_readwrite_db


logger = logging.getLogger(__name__)


@shared_task
def update_recent_events():
    """
    Compute recent events and other statistics and cache them.
    """
    logger.debug("update_recent_events: started")

    try:
        # No middleware on tasks, so this won't get set otherwise.
        # Tell the DB router this thread only needs to read the DB, not write.
        # We run this task frequently, so it's worthwhile.
        set_thread_readonly_db()

        votes = Vote.objects.select_related(
            "voter", "voter__user", "submission").exclude(
            voter=F('submission__voter')).order_by("-id")[:10]
        submissions = Submission.objects.select_related(
            "voter", "voter__user").order_by("-id")[:10]

        entries = list(votes) + list(submissions)
        entries = sorted(entries, key=lambda x: x.created_at, reverse=True)[:10]

        cache.set(RECENT_EVENTS_CACHE_ENTRY, entries, 300)

        number_of_votes = Vote.objects.count()
        cache.set(NUMBER_OF_VOTES_CACHE_ENTRY, number_of_votes, 300)

        logger.debug("There are %d entries" % len(entries))
        logger.debug("There are %d votes" % number_of_votes)
    finally:
        # Be a good citizen and reset the worker's thread to the default state
        set_thread_readwrite_db()
