"""Seed synthetic behavior events untuk demo recommendation engine."""
from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.produk.models import Product
from apps.rekomendasi.models import BehaviorEvent

# (email, password, preferensi) — universe/grade yang disukai untuk filter produk
DEMO_PROFILES = [
    ('ce_fan@harohub.id',  'Demo123!', {'timeline': 'ce',  'grade': 'rg'}),
    ('uc_fan@harohub.id',  'Demo123!', {'timeline': 'uc',  'grade': 'mg'}),
    ('pd_fan@harohub.id',  'Demo123!', {'timeline': 'pd',  'grade': 'hg'}),
    ('mixed@harohub.id',   'Demo123!', {'timeline': None,  'grade': 'mg'}),
]


class Command(BaseCommand):
    help = 'Seed synthetic behavior events untuk demo recommendation engine.'

    def handle(self, *args, **options):
        total_events = 0

        for email, password, prefs in DEMO_PROFILES:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'first_name': email.split('@')[0], 'is_active': True},
            )
            if created:
                user.set_password(password)
                user.save()

            # Pilih produk sesuai preferensi
            qs = Product.objects.exclude(status='DISCONTINUED').select_related('series__timeline', 'grade')
            if prefs['timeline']:
                matching = list(qs.filter(series__timeline__slug=prefs['timeline']))
                other    = list(qs.exclude(series__timeline__slug=prefs['timeline']))[:3]
            else:
                matching = list(qs.filter(grade__slug=prefs['grade']))
                other    = list(qs.exclude(grade__slug=prefs['grade']))[:3]

            events_to_create = []
            for product in matching[:6]:
                events_to_create.append(BehaviorEvent(user=user, product=product, event_type='VIEW'))
                events_to_create.append(BehaviorEvent(user=user, product=product, event_type='VIEW'))
            for product in matching[:3]:
                events_to_create.append(BehaviorEvent(user=user, product=product, event_type='WISHLIST'))
            for product in matching[:2]:
                events_to_create.append(BehaviorEvent(user=user, product=product, event_type='PURCHASE'))
            for product in other:
                events_to_create.append(BehaviorEvent(user=user, product=product, event_type='VIEW'))

            BehaviorEvent.objects.bulk_create(events_to_create)
            total_events += len(events_to_create)
            self.stdout.write(f'  {email}: {len(events_to_create)} events')

        self.stdout.write(self.style.SUCCESS(f'Selesai: {total_events} synthetic events dibuat.'))
