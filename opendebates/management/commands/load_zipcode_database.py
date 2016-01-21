from django.core.management.base import BaseCommand
from opendebates.models import ZipCode
import csv


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('csv_location', nargs='+')

    def handle(self, *args, **options):
        fp = open(options['csv_location'][0])
        lines = csv.reader(fp)
        for line in lines:
            z = ZipCode(zip=line[0], city=line[1], state=line[2])
            z.save()
