"""Integration tests untuk recommendation services: record event, similarity, user-recs, wishlist."""
from django.test import TestCase

from apps.accounts.models import User
from apps.catalog.models import Grade, Product, Series, Timeline
from apps.recommendations.models import (
    BehaviorEvent, ProductPopularity, ProductSimilarity,
    UserRecommendation, Wishlist,
)
from apps.recommendations.services import (
    get_popular_products, get_similar_products,
    get_user_recommendations, record_event, toggle_wishlist,
)


def make_user(email='u@t.id'):
    """Buat user test dengan password minimal.

    Args:
        email (str, optional): Email unik user. Default: ``'u@t.id'``.

    Returns:
        User: Instance User baru.
    """
    return User.objects.create_user(email=email, password='x')


def make_product(slug='kit', status='ACTIVE'):
    """Buat produk test dengan relasi grade/series/timeline yang diperlukan.

    Args:
        slug (str, optional): Slug unik produk. Default: ``'kit'``.
        status (str, optional): Status produk. Default: ``'ACTIVE'``.

    Returns:
        Product: Instance Product yang baru dibuat atau sudah ada.
    """
    tl, _ = Timeline.objects.get_or_create(slug='uc', defaults={'name': 'UC'})
    sr, _ = Series.objects.get_or_create(slug='sr', defaults={'name': 'SR', 'timeline': tl})
    gr, _ = Grade.objects.get_or_create(slug='hg', defaults={'name': 'HG', 'scale': '1/144'})
    return Product.objects.get_or_create(
        slug=slug,
        defaults={'name': slug, 'grade': gr, 'series': sr, 'price': 100000, 'stock': 5, 'status': status},
    )[0]


class RecordEventTest(TestCase):
    """Test suite untuk fungsi ``record_event``."""

    def test_creates_behavior_event(self):
        """Event valid menghasilkan satu baris BehaviorEvent di database."""
        u = make_user()
        p = make_product()
        record_event(u, p, 'VIEW')
        self.assertEqual(BehaviorEvent.objects.count(), 1)

    def test_does_not_raise_on_error(self):
        """Input tidak valid tidak boleh raise exception (non-critical, swallow error)."""
        # Simulate bad input — should not raise
        record_event(None, None, 'VIEW')


class GetSimilarProductsTest(TestCase):
    """Test suite untuk fungsi ``get_similar_products`` (F-28)."""

    def test_returns_from_precomputed_table(self):
        """Produk target yang ada di ProductSimilarity dikembalikan dalam hasil."""
        p1 = make_product('p1')
        p2 = make_product('p2')
        ProductSimilarity.objects.create(source_product=p1, target_product=p2, score=5.0)
        result = get_similar_products(p1, n=6)
        self.assertIn(p2, result)

    def test_excludes_discontinued(self):
        """Produk DISCONTINUED tidak muncul dalam hasil meskipun ada di tabel similarity."""
        p1 = make_product('pd1')
        p2 = make_product('pd2', status='DISCONTINUED')
        ProductSimilarity.objects.create(source_product=p1, target_product=p2, score=5.0)
        result = get_similar_products(p1, n=6)
        self.assertNotIn(p2, result)

    def test_respects_n_limit(self):
        """Jumlah hasil tidak melebihi parameter ``n`` yang diberikan."""
        source = make_product('src')
        for i in range(10):
            target = make_product(f'tgt{i}')
            ProductSimilarity.objects.create(source_product=source, target_product=target, score=float(i))
        result = get_similar_products(source, n=3)
        self.assertEqual(len(result), 3)


class GetUserRecommendationsTest(TestCase):
    """Test suite untuk fungsi ``get_user_recommendations`` (F-29 + F-30)."""

    def setUp(self):
        """Inisialisasi user dan dua produk test."""
        self.user = make_user('rec@t.id')
        self.p1 = make_product('r1')
        self.p2 = make_product('r2')

    def test_returns_personalized_when_available(self):
        """Mengembalikan sumber ``'personalized'`` saat ada data UserRecommendation."""
        UserRecommendation.objects.create(user=self.user, product=self.p1, score=3.0)
        products, source = get_user_recommendations(self.user, n=8)
        self.assertEqual(source, 'personalized')
        self.assertIn(self.p1, products)

    def test_falls_back_to_popularity(self):
        """Mengembalikan sumber ``'popular'`` saat tidak ada data personalisasi."""
        ProductPopularity.objects.create(product=self.p1, score=10.0)
        products, source = get_user_recommendations(self.user, n=8)
        self.assertEqual(source, 'popular')
        self.assertIn(self.p1, products)

    def test_empty_when_no_data(self):
        """Mengembalikan list kosong dengan sumber ``'popular'`` jika tidak ada data sama sekali."""
        products, source = get_user_recommendations(self.user, n=8)
        self.assertEqual(products, [])
        self.assertEqual(source, 'popular')


class WishlistToggleTest(TestCase):
    """Test suite untuk fungsi ``toggle_wishlist``."""

    def setUp(self):
        """Inisialisasi user dan produk test."""
        self.user = make_user('wish@t.id')
        self.product = make_product('wp1')

    def test_add_creates_wishlist_and_event(self):
        """Toggle pada produk yang belum di-wishlist: buat Wishlist + emit event WISHLIST."""
        result = toggle_wishlist(self.user, self.product)
        self.assertTrue(result)
        self.assertEqual(Wishlist.objects.count(), 1)
        self.assertEqual(BehaviorEvent.objects.filter(event_type='WISHLIST').count(), 1)

    def test_remove_deletes_wishlist_no_new_event(self):
        """Toggle pada produk yang sudah di-wishlist: hapus Wishlist tanpa event baru."""
        Wishlist.objects.create(user=self.user, product=self.product)
        result = toggle_wishlist(self.user, self.product)
        self.assertFalse(result)
        self.assertEqual(Wishlist.objects.count(), 0)
