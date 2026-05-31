from .types import Event, ProductAttrs, PreferenceProfile, ScoredProduct


def build_profile(
    events: list,
    attrs_index: dict,
    weights: dict,
) -> PreferenceProfile:
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
