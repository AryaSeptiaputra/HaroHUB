"""Dataclass murni untuk input/output engine rekomendasi — zero ORM, unit-testable tanpa database."""
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductAttrs:
    """Atribut produk yang dibutuhkan engine untuk komputasi similarity dan scoring.

    Frozen dataclass — immutable setelah dibuat, aman dipakai sebagai dict key.

    Attributes:
        id (int): Primary key produk di database.
        grade_id (int): Primary key Grade produk.
        series_id (int): Primary key Series produk.
        timeline_id (int): Primary key Timeline induk series (diturunkan, bukan FK langsung).
    """

    id: int
    grade_id: int
    series_id: int
    timeline_id: int


@dataclass(frozen=True)
class Event:
    """Representasi satu event perilaku user yang sudah dinormalisasi dari database.

    Frozen dataclass — immutable, aman dipakai dalam list dan dict.

    Attributes:
        product_id (int): Primary key produk yang di-interact.
        event_type (str): Jenis event: ``'VIEW'``, ``'WISHLIST'``, atau ``'PURCHASE'``.
    """

    product_id: int
    event_type: str  # 'VIEW' | 'WISHLIST' | 'PURCHASE'


@dataclass
class PreferenceProfile:
    """Profil preferensi user yang dibangun dari agregasi event.

    Setiap dict berisi mapping ``dimension_id → normalized_score`` (0.0–1.0).
    Score dinormalisasi max-normalize sehingga nilai tertinggi selalu 1.0.

    Attributes:
        timeline (dict): Skor preferensi per timeline_id.
        grade (dict): Skor preferensi per grade_id.
        series (dict): Skor preferensi per series_id.
    """

    timeline: dict
    grade: dict
    series: dict


@dataclass
class ScoredProduct:
    """Produk dengan skor relevansi hasil komputasi engine F-29.

    Attributes:
        product_id (int): Primary key produk.
        score (float): Skor relevansi total; semakin tinggi semakin relevan.
        reason (str): Label human-readable dimensi terkuat penyumbang skor.
    """

    product_id: int
    score: float
    reason: str
