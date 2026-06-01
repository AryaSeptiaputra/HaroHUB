"""Management command batch harian: compute F-28/F-29/F-30 dan tulis atomik ke tabel serve."""
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.order.models import OrderItem, OrderStatus
from apps.catalog.models import Product, ProductStatus
from apps.recommendations.engine.popularity import compute_popularity
from apps.recommendations.engine.profile import build_profile, score_products
from apps.recommendations.engine.similarity import compute_similarities
from apps.recommendations.engine.types import Event, ProductAttrs
from apps.recommendations.models import (
    BehaviorEvent, ProductPopularity, ProductSimilarity, UserRecommendation,
)

_COMPLETED_STATUSES = [
    OrderStatus.PAID, OrderStatus.PROCESSING,
    OrderStatus.SHIPPED, OrderStatus.COMPLETED,
]


class Command(BaseCommand):
    """Management command untuk menghitung ulang semua tabel serve rekomendasi.

    Menjalankan tiga komputasi dalam satu transaksi atomik:
    - **F-28** ``ProductSimilarity``: skor kemiripan antar produk.
    - **F-29** ``UserRecommendation``: rekomendasi personal per user.
    - **F-30** ``ProductPopularity``: skor popularitas global.

    Tabel serve yang lama di-truncate sebelum data baru di-insert (full rebuild).
    Dijadwalkan cron harian jam 02:00.

    Hyperparameter diambil dari ``settings.py``:
    - ``RECOMMENDATION_WEIGHTS``: bobot event (VIEW/WISHLIST/PURCHASE).
    - ``SIMILARITY_WEIGHTS``: bobot dimensi untuk F-28.
    - ``RECOMMENDATION_DIMENSION_WEIGHTS``: bobot dimensi untuk F-29.
    - ``SIMILARITY_TOP_K``: max kandidat serupa per produk.
    - ``RECOMMENDATION_TOP_N``: max rekomendasi per user.
    """

    help = 'Compute F-28 similarity, F-29 user recommendations, F-30 popularity.'

    def handle(self, *args, **options):
        """Eksekusi penuh komputasi rekomendasi dan tulis hasilnya ke database.

        Args:
            *args: Argumen positional dari management command (tidak dipakai).
            **options: Opsi dari management command (termasuk ``verbosity``).
        """
        weights     = settings.RECOMMENDATION_WEIGHTS
        sim_weights = settings.SIMILARITY_WEIGHTS
        dim_weights = settings.RECOMMENDATION_DIMENSION_WEIGHTS
        top_k       = settings.SIMILARITY_TOP_K
        top_n       = settings.RECOMMENDATION_TOP_N

        # ── Fetch products ────────────────────────────────────────────────────
        self.stdout.write('Fetching products...')
        products_qs = (
            Product.objects
            .exclude(status=ProductStatus.DISCONTINUED)
            .select_related('grade', 'series__timeline')
        )
        product_attrs = [
            ProductAttrs(
                id=p.id,
                grade_id=p.grade_id,
                series_id=p.series_id,
                timeline_id=p.series.timeline_id,
            )
            for p in products_qs
        ]
        attrs_index = {a.id: a for a in product_attrs}
        self.stdout.write(f'  {len(product_attrs)} produk aktif.')

        # ── Fetch events ──────────────────────────────────────────────────────
        self.stdout.write('Fetching behavior events...')
        user_events: dict = defaultdict(list)
        all_events: list  = []
        for user_id, product_id, event_type in (
            BehaviorEvent.objects.values_list('user_id', 'product_id', 'event_type')
        ):
            e = Event(product_id=product_id, event_type=event_type)
            user_events[user_id].append(e)
            all_events.append(e)
        self.stdout.write(f'  {len(all_events)} events dari {len(user_events)} user.')

        # ── Fetch purchased product IDs per user (exclude dari F-29) ─────────
        purchased: dict = defaultdict(set)
        for row in OrderItem.objects.filter(
            order__status__in=_COMPLETED_STATUSES
        ).values('order__user_id', 'product_id'):
            purchased[row['order__user_id']].add(row['product_id'])

        # ── Atomic rewrite semua tabel serve ─────────────────────────────────
        with transaction.atomic():

            # F-28 ─────────────────────────────────────────────────────────────
            self.stdout.write('Computing F-28 ProductSimilarity...')
            sim_map = compute_similarities(product_attrs, sim_weights, top_k)
            ProductSimilarity.objects.all().delete()
            sim_rows = [
                ProductSimilarity(source_product_id=src, target_product_id=tgt, score=score)
                for src, targets in sim_map.items()
                for tgt, score in targets
            ]
            ProductSimilarity.objects.bulk_create(sim_rows, batch_size=1000)
            self.stdout.write(f'  {len(sim_rows)} similarity pairs.')

            # F-30 ─────────────────────────────────────────────────────────────
            self.stdout.write('Computing F-30 ProductPopularity...')
            pop_scores = compute_popularity(all_events, weights)
            ProductPopularity.objects.all().delete()
            pop_rows = [
                ProductPopularity(product_id=pid, score=score)
                for pid, score in pop_scores.items()
                if pid in attrs_index
            ]
            ProductPopularity.objects.bulk_create(pop_rows, batch_size=1000)
            self.stdout.write(f'  {len(pop_rows)} popularity scores.')

            # F-29 ─────────────────────────────────────────────────────────────
            self.stdout.write('Computing F-29 UserRecommendation...')
            UserRecommendation.objects.all().delete()
            rec_rows = []
            for user_id, events in user_events.items():
                profile = build_profile(events, attrs_index, weights)
                exclude = purchased.get(user_id, set())
                scored  = score_products(profile, product_attrs, dim_weights, top_n, exclude)
                for sp in scored:
                    rec_rows.append(UserRecommendation(
                        user_id=user_id,
                        product_id=sp.product_id,
                        score=sp.score,
                        reason=sp.reason,
                    ))
            UserRecommendation.objects.bulk_create(rec_rows, batch_size=1000)
            self.stdout.write(f'  {len(rec_rows)} recommendation rows ({len(user_events)} users).')

        self.stdout.write(self.style.SUCCESS('compute_recommendations selesai.'))
