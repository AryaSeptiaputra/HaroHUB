from .types import ProductAttrs


def pair_score(a: ProductAttrs, b: ProductAttrs, weights: dict) -> float:
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
