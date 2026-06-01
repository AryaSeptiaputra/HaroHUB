"""Unit tests untuk recommendation engine — berjalan tanpa database (SimpleTestCase)."""
from django.test import SimpleTestCase

from apps.recommendations.engine.types import ProductAttrs, Event
from apps.recommendations.engine.similarity import pair_score, compute_similarities
from apps.recommendations.engine.profile import build_profile, score_products
from apps.recommendations.engine.popularity import compute_popularity

WEIGHTS = {'series': 3, 'timeline': 2, 'grade': 1}
EVENT_WEIGHTS = {'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}


class PairScoreTest(SimpleTestCase):
    """Test suite untuk fungsi ``pair_score`` — skor kemiripan dua produk."""

    def _p(self, grade, series, timeline):
        """Helper: buat ProductAttrs dengan id=0 dan atribut yang diberikan.

        Args:
            grade (int): Grade ID.
            series (int): Series ID.
            timeline (int): Timeline ID.

        Returns:
            ProductAttrs: Instance dengan id=0.
        """
        return ProductAttrs(id=0, grade_id=grade, series_id=series, timeline_id=timeline)

    def test_same_series_and_timeline(self):
        """Produk dengan series dan timeline sama menghasilkan skor series(3) + timeline(2) = 5."""
        a = self._p(1, 1, 1)
        b = self._p(2, 1, 1)
        self.assertEqual(pair_score(a, b, WEIGHTS), 5.0)  # series(3) + timeline(2)

    def test_same_all(self):
        """Produk identik menghasilkan skor maksimal series(3) + timeline(2) + grade(1) = 6."""
        a = self._p(1, 1, 1)
        self.assertEqual(pair_score(a, a, WEIGHTS), 6.0)

    def test_no_overlap(self):
        """Produk tanpa overlap atribut menghasilkan skor 0."""
        a = self._p(1, 1, 1)
        b = self._p(2, 2, 2)
        self.assertEqual(pair_score(a, b, WEIGHTS), 0.0)

    def test_grade_only(self):
        """Produk dengan hanya grade yang sama menghasilkan skor grade(1) = 1."""
        a = self._p(1, 1, 1)
        b = self._p(1, 2, 2)
        self.assertEqual(pair_score(a, b, WEIGHTS), 1.0)


class PopularityTest(SimpleTestCase):
    """Test suite untuk fungsi ``compute_popularity`` — skor popularitas dari events."""

    def test_weighted_counts(self):
        """Skor dihitung sebagai jumlah bobot event per produk."""
        events = [
            Event(product_id=1, event_type='VIEW'),
            Event(product_id=1, event_type='PURCHASE'),
            Event(product_id=2, event_type='WISHLIST'),
        ]
        scores = compute_popularity(events, EVENT_WEIGHTS)
        self.assertEqual(scores[1], 6)   # 1 + 5
        self.assertEqual(scores[2], 3)   # 3
