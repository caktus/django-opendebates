from django.core.management.base import BaseCommand

from opendebates.tasks import update_recent_events


class Command(BaseCommand):
    def handle(self, *args, **options):
        update_recent_events()
