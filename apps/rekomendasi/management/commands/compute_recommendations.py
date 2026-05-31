from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Compute and store recommendation scores (F-28, F-29, F-30).'

    def handle(self, *args, **options):
        self.stdout.write('compute_recommendations: belum diimplementasikan.')
