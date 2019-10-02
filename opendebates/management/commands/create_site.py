from django.contrib.sites.models import Site
from django.core.management.base import LabelCommand


class Command(LabelCommand):
    def handle(self, *labels, **options):
        for label in labels:
            print(label)
            Site.objects.get_or_create(name=label, domain=label)
