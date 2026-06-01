"""Engine F-30: hitung skor popularitas produk dari agregat weighted events."""
from .types import Event


def compute_popularity(events: list, weights: dict) -> dict:
    """Hitung skor popularitas setiap produk dari semua event yang ada.

    Skor adalah penjumlahan bobot event per produk. Event dengan bobot 0
    (tidak ada di dict ``weights``) di-skip sepenuhnya.

    Args:
        events (list[Event]): Semua event dari semua user (bukan per-user).
        weights (dict): Bobot per event type,
            contoh: ``{'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}``.

    Returns:
        dict[int, float]: Mapping ``product_id → total_score``.
            Produk yang tidak punya event sama sekali tidak muncul di hasil.
    """
    scores: dict = {}
    for event in events:
        w = weights.get(event.event_type, 0)
        if w == 0:
            continue
        scores[event.product_id] = scores.get(event.product_id, 0) + w
    return scores
