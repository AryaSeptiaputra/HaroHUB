from apps.produk.models import ProductStatus

from .models import (
    BehaviorEvent, EventType, ProductPopularity,
    ProductSimilarity, UserRecommendation, Wishlist,
)

_ACTIVE_STATUSES = [ProductStatus.ACTIVE, ProductStatus.PRE_ORDER]


# ── Capture (write-path) ──────────────────────────────────────────────────────

def record_event(user, product, event_type):
    """Append-only INSERT ke BehaviorEvent. Non-critical — tidak boleh break request."""
    try:
        BehaviorEvent.objects.create(user=user, product=product, event_type=event_type)
    except Exception:
        pass


# ── Serve (read-path) ─────────────────────────────────────────────────────────

def get_similar_products(product, n=6):
    """F-28: Kembalikan top-N produk serupa dari tabel precomputed."""
    sims = (
        ProductSimilarity.objects
        .filter(source_product=product, target_product__status__in=_ACTIVE_STATUSES)
        .select_related('target_product__grade', 'target_product__series__timeline')
        .prefetch_related('target_product__images')
        .order_by('-score')[:n]
    )
    return [s.target_product for s in sims]


def get_user_recommendations(user, n=8):
    """F-29 + F-30: Personalized jika data ada, fallback ke popularitas (cold-start)."""
    recs = list(
        UserRecommendation.objects
        .filter(user=user, product__status__in=_ACTIVE_STATUSES)
        .select_related('product__grade', 'product__series__timeline')
        .prefetch_related('product__images')
        .order_by('-score')[:n]
    )
    if recs:
        return [r.product for r in recs], 'personalized'

    # Cold-start: popularity fallback
    pops = list(
        ProductPopularity.objects
        .filter(product__status__in=_ACTIVE_STATUSES)
        .select_related('product__grade', 'product__series__timeline')
        .prefetch_related('product__images')
        .order_by('-score')[:n]
    )
    return [p.product for p in pops], 'popular'


def get_popular_products(n=8):
    """F-30: Produk terpopuler — untuk guest/anonymous."""
    pops = list(
        ProductPopularity.objects
        .filter(product__status__in=_ACTIVE_STATUSES)
        .select_related('product__grade', 'product__series__timeline')
        .prefetch_related('product__images')
        .order_by('-score')[:n]
    )
    return [p.product for p in pops]


def toggle_wishlist(user, product):
    """Toggle Wishlist + emit WISHLIST event. Kembalikan (is_wishlisted: bool)."""
    item = Wishlist.objects.filter(user=user, product=product).first()
    if item:
        item.delete()
        return False
    Wishlist.objects.create(user=user, product=product)
    record_event(user, product, EventType.WISHLIST)
    return True
