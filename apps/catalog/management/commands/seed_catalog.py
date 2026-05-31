from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Grade, Product, ProductStatus, Series, Timeline


TIMELINES = [
    ('uc', 'Universal Century'),
    ('ce', 'Cosmic Era'),
    ('ad', 'Anno Domini'),
    ('pd', 'Post Disaster'),
    ('as', 'Ad Stella'),
    ('ac', 'After Colony'),
    ('bf', 'Build Fighters'),
]

SERIES = [
    ('mobile-suit-gundam-0079', 'Mobile Suit Gundam 0079', 'uc'),
    ('zeta-gundam', 'Zeta Gundam', 'uc'),
    ('gundam-unicorn', 'Gundam Unicorn', 'uc'),
    ('hathaway', "Hathaway's Flash", 'uc'),
    ('gundam-seed', 'Gundam SEED', 'ce'),
    ('gundam-seed-destiny', 'Gundam SEED Destiny', 'ce'),
    ('gundam-seed-freedom', 'Gundam SEED Freedom', 'ce'),
    ('gundam-00', 'Gundam 00', 'ad'),
    ('iron-blooded-orphans', 'Iron-Blooded Orphans', 'pd'),
    ('witch-from-mercury', 'The Witch from Mercury', 'as'),
    ('gundam-wing', 'Gundam Wing', 'ac'),
    ('build-fighters', 'Build Fighters', 'bf'),
]

GRADES = [
    ('eg', 'Entry Grade', ''),
    ('hg', 'High Grade', '1/144'),
    ('rg', 'Real Grade', '1/144'),
    ('mg', 'Master Grade', '1/100'),
    ('pg', 'Perfect Grade', '1/60'),
    ('sd', 'Super Deformed', ''),
    ('metal-build', 'Metal Build', ''),
]

PRODUCTS = [
    # (name, grade_slug, series_slug, price, stock, status)
    ('HG 1/144 RX-78-2 Gundam', 'hg', 'mobile-suit-gundam-0079', 85000, 15, 'ACTIVE'),
    ('MG 1/100 RX-78-2 Gundam Ver. 3.0', 'mg', 'mobile-suit-gundam-0079', 430000, 8, 'ACTIVE'),
    ('RG 1/144 Zeta Gundam', 'rg', 'zeta-gundam', 295000, 5, 'ACTIVE'),
    ('MG 1/100 MSZ-006 Zeta Gundam Ver. Ka', 'mg', 'zeta-gundam', 520000, 3, 'ACTIVE'),
    ('RG 1/144 RX-0 Unicorn Gundam', 'rg', 'gundam-unicorn', 315000, 10, 'ACTIVE'),
    ('PG 1/60 RX-0 Unicorn Gundam', 'pg', 'gundam-unicorn', 2850000, 2, 'ACTIVE'),
    ('HG 1/144 Aerial', 'hg', 'witch-from-mercury', 130000, 20, 'ACTIVE'),
    ('HG 1/144 Aerial Rebuild', 'hg', 'witch-from-mercury', 145000, 12, 'ACTIVE'),
    ('MG 1/100 ZGMF-X10A Freedom Gundam', 'mg', 'gundam-seed', 460000, 7, 'ACTIVE'),
    ('RG 1/144 ZGMF-X10A Freedom Gundam', 'rg', 'gundam-seed', 275000, 9, 'ACTIVE'),
    ('HG 1/144 ZGMF-X20A Strike Freedom Gundam', 'hg', 'gundam-seed-freedom', 195000, 14, 'ACTIVE'),
    ('MG 1/100 ZGMF-X20A Strike Freedom Gundam Full Burst Mode', 'mg', 'gundam-seed-freedom', 680000, 4, 'PRE_ORDER'),
    ('HG 1/144 GN-001 Gundam Exia', 'hg', 'gundam-00', 120000, 11, 'ACTIVE'),
    ('MG 1/100 GN-001REII Gundam Exia Repair II', 'mg', 'gundam-00', 490000, 3, 'ACTIVE'),
    ('HG 1/144 ASW-G-08 Gundam Barbatos', 'hg', 'iron-blooded-orphans', 140000, 18, 'ACTIVE'),
    ('MG 1/100 ASW-G-08 Gundam Barbatos', 'mg', 'iron-blooded-orphans', 520000, 5, 'ACTIVE'),
    ("RG 1/144 Wing Gundam Zero EW", 'rg', 'gundam-wing', 335000, 6, 'ACTIVE'),
    ("MG 1/100 Wing Gundam Zero EW Ver. Ka", 'mg', 'gundam-wing', 590000, 2, 'PRE_ORDER'),
    ('HG 1/144 Xi Gundam', 'hg', 'hathaway', 185000, 8, 'ACTIVE'),
    ('HG 1/144 Penelope', 'hg', 'hathaway', 185000, 6, 'ACTIVE'),
    ('EG 1/144 RX-78-2 Gundam', 'eg', 'mobile-suit-gundam-0079', 65000, 25, 'ACTIVE'),
    ('SD EX-Standard RX-78-2 Gundam', 'sd', 'mobile-suit-gundam-0079', 75000, 30, 'ACTIVE'),
    ('Metal Build Destiny Gundam Soul Red', 'metal-build', 'gundam-seed-destiny', 3200000, 1, 'PRE_ORDER'),
    ('HG 1/144 Gundam Lfrith', 'hg', 'witch-from-mercury', 125000, 16, 'ACTIVE'),
]


class Command(BaseCommand):
    help = 'Seed data referensi produk (grade, timeline, series) dan contoh produk.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding timelines...')
        timeline_map = {}
        for slug, name in TIMELINES:
            obj, _ = Timeline.objects.get_or_create(slug=slug, defaults={'name': name})
            timeline_map[slug] = obj

        self.stdout.write('Seeding series...')
        series_map = {}
        for slug, name, tl_slug in SERIES:
            obj, _ = Series.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'timeline': timeline_map[tl_slug]},
            )
            series_map[slug] = obj

        self.stdout.write('Seeding grades...')
        grade_map = {}
        for slug, name, scale in GRADES:
            obj, _ = Grade.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'scale': scale},
            )
            grade_map[slug] = obj

        self.stdout.write('Seeding products...')
        count = 0
        for name, grade_slug, series_slug, price, stock, status in PRODUCTS:
            slug = slugify(name)
            _, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'grade': grade_map[grade_slug],
                    'series': series_map[series_slug],
                    'price': price,
                    'stock': stock,
                    'status': status,
                    'description': f'{name}. Kit plastik model Gunpla dari Bandai.',
                },
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Selesai: {len(TIMELINES)} timeline, {len(SERIES)} seri, '
            f'{len(GRADES)} grade, {count} produk baru dibuat.'
        ))
