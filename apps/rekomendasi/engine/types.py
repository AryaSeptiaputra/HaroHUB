from dataclasses import dataclass


@dataclass(frozen=True)
class ProductAttrs:
    id: int
    grade_id: int
    series_id: int
    timeline_id: int


@dataclass(frozen=True)
class Event:
    product_id: int
    event_type: str  # 'VIEW' | 'WISHLIST' | 'PURCHASE'


@dataclass
class PreferenceProfile:
    timeline: dict
    grade: dict
    series: dict


@dataclass
class ScoredProduct:
    product_id: int
    score: float
    reason: str
