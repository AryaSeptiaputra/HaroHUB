"""Service layer rekomendasi: record event, serve similarity/user-recs/popularitas, toggle wishlist."""
from apps.catalog.models import ProductStatus

from .models import (
    BehaviorEvent, EventType, ProductPopularity,
    ProductSimilarity, UserRecommendation, Wishlist,
)

_ACTIVE_STATUSES = [ProductStatus.ACTIVE, ProductStatus.PRE_ORDER]


# ── Capture (write-path) ──────────────────────────────────────────────────────

def record_event(user, product, event_type):
    """Catat satu event perilaku user ke BehaviorEvent (append-only INSERT).

    Non-critical: exception yang terjadi di dalam fungsi ini di-swallow agar
    tidak mengganggu request utama (view detail produk, checkout, dsb.).

    Args:
        user (User): User yang melakukan event.
        product (Product): Produk yang di-interact.
        event_type (str): Jenis event; salah satu dari ``'VIEW'``, ``'WISHLIST'``, ``'PURCHASE'``.
    """
    try:
        BehaviorEvent.objects.create(user=user, product=product, event_type=event_type)
    except Exception:
        pass


# ── Serve (read-path) ─────────────────────────────────────────────────────────

def get_similar_products(product, n=6):
    """F-28: Kembalikan top-N produk serupa dari tabel precomputed ProductSimilarity.

    Hanya mengembalikan produk dengan status ACTIVE atau PRE_ORDER. Produk
    DISCONTINUED tidak muncul meskipun ada di tabel similarity.

    Args:
        product (Product): Produk referensi yang ingin dicari produk serupanya.
        n (int, optional): Jumlah maksimum produk yang dikembalikan. Default: 6.

    Returns:
        list[Product]: List instance Product yang mirip, diurutkan skor tertinggi.
            List kosong jika belum ada data similarity atau semua target discontinued.
    """
    sims = (
        ProductSimilarity.objects
        .filter(source_product=product, target_product__status__in=_ACTIVE_STATUSES)
        .select_related('target_product__grade', 'target_product__series__timeline')
        .prefetch_related('target_product__images')
        .order_by('-score')[:n]
    )
    return [s.target_product for s in sims]


def get_user_recommendations(user, n=8):
    """F-29 + F-30: Kembalikan rekomendasi personal atau fallback popularitas.

    Urutan prioritas:
    1. Personalized (F-29): jika ada data ``UserRecommendation`` untuk user ini.
    2. Popular (F-30): cold-start fallback jika belum ada data personalisasi.

    Args:
        user (User): User yang akan menerima rekomendasi.
        n (int, optional): Jumlah maksimum produk yang dikembalikan. Default: 8.

    Returns:
        tuple[list[Product], str]: Tuple berisi:
            - List instance Product yang direkomendasikan.
            - String source: ``'personalized'`` atau ``'popular'``.
    """
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
    """F-30: Kembalikan produk terpopuler untuk guest/anonymous user.

    Digunakan di widget "Untuk Kamu" saat user belum login.

    Args:
        n (int, optional): Jumlah maksimum produk yang dikembalikan. Default: 8.

    Returns:
        list[Product]: List instance Product diurutkan skor popularitas tertinggi.
            List kosong jika tabel ProductPopularity belum di-compute.
    """
    pops = list(
        ProductPopularity.objects
        .filter(product__status__in=_ACTIVE_STATUSES)
        .select_related('product__grade', 'product__series__timeline')
        .prefetch_related('product__images')
        .order_by('-score')[:n]
    )
    return [p.product for p in pops]


def toggle_wishlist(user, product):
    """Toggle status wishlist: tambah jika belum ada, hapus jika sudah ada.

    Saat menambahkan, emit event WISHLIST ke BehaviorEvent untuk signal engine.
    Saat menghapus, tidak ada event baru yang di-emit.

    Args:
        user (User): User pemilik wishlist.
        product (Product): Produk yang akan di-toggle.

    Returns:
        bool: ``True`` jika produk sekarang ada di wishlist (baru ditambahkan),
              ``False`` jika produk baru saja dihapus dari wishlist.
    """
    item = Wishlist.objects.filter(user=user, product=product).first()
    if item:
        item.delete()
        return False
    Wishlist.objects.create(user=user, product=product)
    record_event(user, product, EventType.WISHLIST)
    return True
