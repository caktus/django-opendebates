from django.core.management.base import BaseCommand

from opendebates.tasks import update_trending_scores


class Command(BaseCommand):
    def handle(self, *args, **options):
        update_trending_scores()
