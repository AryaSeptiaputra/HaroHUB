from django.core.management.base import BaseCommand

from apps.order.models import ShippingRate

RATES = [
    ('Jakarta',    15000, '1-2'),
    ('Bogor',      15000, '1-2'),
    ('Depok',      15000, '1-2'),
    ('Tangerang',  15000, '1-2'),
    ('Bekasi',     15000, '1-2'),
    ('Bandung',    18000, '2-3'),
    ('Semarang',   20000, '2-3'),
    ('Yogyakarta', 20000, '2-3'),
    ('Surabaya',   25000, '3-4'),
    ('Malang',     25000, '3-4'),
    ('Bali',       28000, '3-4'),
    ('Medan',      35000, '4-5'),
    ('Palembang',  30000, '3-5'),
    ('Makassar',   35000, '4-5'),
    ('Balikpapan', 32000, '4-5'),
    ('Manado',     38000, '5-6'),
]


class Command(BaseCommand):
    help = 'Seed ongkos kirim mock per kota.'

    def handle(self, *args, **options):
        count = 0
        for city, cost, days in RATES:
            _, created = ShippingRate.objects.get_or_create(
                city=city,
                defaults={'cost': cost, 'estimated_days': days},
            )
            if created:
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Selesai: {count} ongkir baru ditambahkan.'))
