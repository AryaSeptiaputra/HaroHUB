"""Engine F-29: bangun profil preferensi user dari event dan skor kandidat produk."""
from .types import Event, ProductAttrs, PreferenceProfile, ScoredProduct


def build_profile(
    events: list,
    attrs_index: dict,
    weights: dict,
) -> PreferenceProfile:
    """Bangun profil preferensi user dari riwayat event perilaku.

    Setiap event diberi bobot sesuai jenis (VIEW/WISHLIST/PURCHASE) lalu diakumulasi
    per dimensi (timeline, grade, series). Hasil akhir dinormalisasi dengan max-normalize
    sehingga nilai tertinggi selalu 1.0.

    Event dengan ``event_type`` yang tidak ada di ``weights`` (bobot 0) di-skip.
    Event untuk produk yang tidak ada di ``attrs_index`` juga di-skip.

    Args:
        events (list[Event]): Semua event milik satu user.
        attrs_index (dict[int, ProductAttrs]): Mapping ``product_id → ProductAttrs``
            untuk semua produk aktif.
        weights (dict): Bobot per event type, contoh: ``{'VIEW': 1, 'WISHLIST': 3, 'PURCHASE': 5}``.

    Returns:
        PreferenceProfile: Profil preferensi dengan skor per dimensi yang sudah dinormalisasi.
            Dict kosong pada dimensi yang tidak ada event-nya sama sekali.
    """
    timeline_scores: dict = {}
    grade_scores: dict = {}
    series_scores: dict = {}

    for event in events:
        w = weights.get(event.event_type, 0)
        attrs = attrs_index.get(event.product_id)
        if not attrs or w == 0:
            continue
        timeline_scores[attrs.timeline_id] = timeline_scores.get(attrs.timeline_id, 0) + w
        grade_scores[attrs.grade_id] = grade_scores.get(attrs.grade_id, 0) + w
        series_scores[attrs.series_id] = series_scores.get(attrs.series_id, 0) + w

    def max_normalize(d: dict) -> dict:
        """Normalisasi dict skor sehingga nilai terbesar menjadi 1.0.

        Args:
            d (dict): Dict ``id → raw_score`` yang akan dinormalisasi.

        Returns:
            dict: Dict ``id → normalized_score`` (0.0–1.0), atau dict kosong jika input kosong.
        """
        if not d:
            return {}
        max_val = max(d.values())
        return {k: v / max_val for k, v in d.items()}

    return PreferenceProfile(
        timeline=max_normalize(timeline_scores),
        grade=max_normalize(grade_scores),
        series=max_normalize(series_scores),
    )


def score_products(
    profile: PreferenceProfile,
    candidates: list,
    dim_weights: dict,
    top_n: int,
    exclude_ids: set,
) -> list:
    """Skor semua kandidat produk berdasarkan profil preferensi user.

    Skor dihitung dengan mengalikan skor profil per dimensi dengan bobot dimensi.
    Produk dengan skor 0 (tidak ada overlap dengan profil) tidak disertakan.
    Reason ditentukan dari dimensi dengan kontribusi skor terbesar.

    Args:
        profile (PreferenceProfile): Profil preferensi user hasil ``build_profile()``.
        candidates (list[ProductAttrs]): Semua produk kandidat untuk di-skor.
        dim_weights (dict): Bobot per dimensi saat scoring,
            contoh: ``{'series': 3, 'timeline': 2, 'grade': 1}``.
        top_n (int): Jumlah maksimum produk yang dikembalikan.
        exclude_ids (set[int]): Set ``product_id`` yang dikecualikan dari hasil
            (biasanya produk yang sudah dibeli user).

    Returns:
        list[ScoredProduct]: List produk dengan skor, diurutkan skor tertinggi, maks ``top_n`` entri.
    """
    scored = []
    for attrs in candidates:
        if attrs.id in exclude_ids:
            continue

        s_series = profile.series.get(attrs.series_id, 0) * dim_weights.get('series', 3)
        s_timeline = profile.timeline.get(attrs.timeline_id, 0) * dim_weights.get('timeline', 2)
        s_grade = profile.grade.get(attrs.grade_id, 0) * dim_weights.get('grade', 1)
        total = s_series + s_timeline + s_grade

        if total == 0:
            continue

        # Reason: dimensi penyumbang terbesar (ties: series > timeline > grade)
        contributions = [
            ('series', s_series),
            ('timeline', s_timeline),
            ('grade', s_grade),
        ]
        top_dim = max(contributions, key=lambda x: x[1])[0]
        reason = {
            'series': 'Karena kamu menyukai seri ini',
            'timeline': 'Karena kamu menyukai universe ini',
            'grade': 'Karena kamu menyukai grade ini',
        }[top_dim]

        scored.append(ScoredProduct(product_id=attrs.id, score=total, reason=reason))

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_n]
