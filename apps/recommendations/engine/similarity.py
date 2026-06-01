"""Engine F-28: hitung skor kemiripan antar produk berdasarkan overlap atribut (series, timeline, grade)."""
from .types import ProductAttrs


def pair_score(a: ProductAttrs, b: ProductAttrs, weights: dict) -> float:
    """Hitung skor kemiripan antara dua produk berdasarkan overlap atribut.

    Skor merupakan jumlah bobot dari setiap dimensi yang sama antara kedua produk.
    Hierarki bobot default: series (3) > timeline (2) > grade (1).

    Args:
        a (ProductAttrs): Atribut produk pertama.
        b (ProductAttrs): Atribut produk kedua.
        weights (dict): Bobot per dimensi, contoh: ``{'series': 3, 'timeline': 2, 'grade': 1}``.

    Returns:
        float: Skor kemiripan (0.0 jika tidak ada overlap, maks = jumlah semua bobot).
    """
    score = 0.0
    if a.series_id == b.series_id:
        score += weights.get('series', 3)
    if a.timeline_id == b.timeline_id:
        score += weights.get('timeline', 2)
    if a.grade_id == b.grade_id:
        score += weights.get('grade', 1)
    return score


def compute_similarities(
    products: list,
    weights: dict,
    top_k: int,
) -> dict:
    """Hitung skor kemiripan semua pasangan produk dan kembalikan top-K per produk.

    Kompleksitas O(n²) — dirancang untuk dijalankan secara offline (batch command),
    bukan di request path. Produk tidak dibandingkan dengan dirinya sendiri (i == j di-skip).

    Args:
        products (list[ProductAttrs]): List atribut semua produk aktif.
        weights (dict): Bobot per dimensi; diteruskan ke ``pair_score()``.
        top_k (int): Jumlah maksimum produk serupa yang disimpan per produk sumber.

    Returns:
        dict[int, list[tuple[int, float]]]: Mapping ``source_product_id → [(target_id, score), ...]``
            diurutkan skor tertinggi, maks ``top_k`` entri per source.
            Pasangan dengan skor 0 tidak disertakan.
    """
    result = {}
    for i, source in enumerate(products):
        scored = []
        for j, target in enumerate(products):
            if i == j:
                continue
            score = pair_score(source, target, weights)
            if score > 0:
                scored.append((target.id, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        result[source.id] = scored[:top_k]
    return result
