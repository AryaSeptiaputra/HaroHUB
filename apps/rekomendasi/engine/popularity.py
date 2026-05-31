from .types import Event


def compute_popularity(events: list, weights: dict) -> dict:
    scores: dict = {}
    for event in events:
        w = weights.get(event.event_type, 0)
        if w == 0:
            continue
        scores[event.product_id] = scores.get(event.product_id, 0) + w
    return scores
