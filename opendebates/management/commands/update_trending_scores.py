from django.core.management.base import BaseCommand
from django.db import connection

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


class Command(BaseCommand):
    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(sql)
            cursor.execute(sql2)
