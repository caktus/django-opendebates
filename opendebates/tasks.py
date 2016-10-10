from __future__ import absolute_import
import logging

from celery import shared_task
from django.core.cache import cache
from django.core import management
from django.db import connection
from django.db.models import F

from opendebates.models import Vote, Submission, RECENT_EVENTS_CACHE_ENTRY, \
    NUMBER_OF_VOTES_CACHE_ENTRY
from opendebates.router import set_thread_readonly_db, set_thread_readwrite_db


sql2 = """
UPDATE opendebates_submission
SET random_id=random()
"""

sql = """
UPDATE opendebates_submission
SET score=q.score
FROM
(
SELECT
s."id",
CASE WHEN
(COUNT(v.id) < 15) THEN 0 ELSE
((Count(v."id") + Sum(CASE WHEN v.created_at > NOW() - INTERVAL '2 HOUR' THEN 1 ELSE 0 END)*200 + Sum(CASE WHEN v.created_at > NOW() - INTERVAL '4 HOUR' THEN 1 ELSE 0 END)*100)) / EXTRACT(EPOCH FROM (NOW() - MIN(s.created_at)))^1.5*(1+RANDOM()) END AS score
FROM
opendebates_submission AS s
INNER JOIN opendebates_vote AS v ON v.submission_id = s."id"
GROUP BY
s."id"
) q
WHERE
q."id" = opendebates_submission."id";
"""  # noqa


logger = logging.getLogger(__name__)


exception_logged = False


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
            "voter", "voter__user", "submission").filter(
            submission__approved=True, submission__duplicate_of__isnull=True).exclude(
            voter=F('submission__voter')).order_by("-id")[:10]
        submissions = Submission.objects.select_related(
            "voter", "voter__user").filter(
            approved=True, duplicate_of__isnull=True).order_by("-id")[:10]

        entries = list(votes) + list(submissions)
        entries = sorted(entries, key=lambda x: x.created_at, reverse=True)[:10]

        cache.set(RECENT_EVENTS_CACHE_ENTRY, entries, 24*3600)

        number_of_votes = Vote.objects.count()
        cache.set(NUMBER_OF_VOTES_CACHE_ENTRY, number_of_votes, 24*3600)

        logger.debug("There are %d entries" % len(entries))
        logger.debug("There are %d votes" % number_of_votes)
    except:
        # This task runs too frequently to report a recurring problem every time
        # it happens.
        global exception_logged
        if not exception_logged:
            logger.exception("Unexpected exception in update_recent_events")
            exception_logged = True
    finally:
        # Be a good citizen and reset the worker's thread to the default state
        set_thread_readwrite_db()


@shared_task
def update_trending_scores():
    logger.debug("update_trending_scores: started")
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute(sql2)
    except:
        logger.exception("Unexpected error in update_trending_scores")


@shared_task(ignore_result=True)
def backup_database():
    """ Backup the database using django-dbbackup """
    logger.info("start database_backup")
    management.call_command('dbbackup', compress=True)
    logger.info("end database_backup")
