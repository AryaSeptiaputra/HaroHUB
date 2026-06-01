"""Model capture layer (BehaviorEvent, Wishlist) dan serve layer (ProductSimilarity, UserRecommendation, ProductPopularity)."""
from django.db import models


class EventType(models.TextChoices):
    """Jenis event perilaku user yang direkam dalam sistem rekomendasi."""

    VIEW     = 'VIEW',     'View'
    WISHLIST = 'WISHLIST', 'Wishlist'
    PURCHASE = 'PURCHASE', 'Purchase'


# ── Capture layer (write-path) ────────────────────────────────────────────────

class BehaviorEvent(models.Model):
    """Append-only event log perilaku user terhadap produk.

    Log ini tidak boleh di-UPDATE atau DELETE (kecuali pruning data lama).
    Event PURCHASE sengaja duplikat dari OrderItem karena keduanya punya
    tujuan berbeda: OrderItem untuk financial record, BehaviorEvent untuk ML signal.

    Bobot event (VIEW/WISHLIST/PURCHASE) tidak disimpan di sini — dikonfigurasi
    di ``settings.RECOMMENDATION_WEIGHTS`` dan diterapkan saat compute time.

    Attributes:
        user (ForeignKey): User yang melakukan event; CASCADE saat user dihapus.
        product (ForeignKey): Produk yang di-interact; CASCADE saat produk dihapus.
        event_type (CharField): Jenis event: ``VIEW``, ``WISHLIST``, atau ``PURCHASE``.
        created_at (DateTimeField): Timestamp event; auto-set saat INSERT.
    """

    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='behavior_events')
    product    = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='behavior_events')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),                   # F-29: agregasi per-user
            models.Index(fields=['product', 'event_type']),  # F-30: popularitas per produk
        ]

    def __str__(self):
        """Return representasi ringkas berisi jenis event, user_id, dan product_id."""
        return f'{self.event_type}({self.user_id}, {self.product_id})'


class Wishlist(models.Model):
    """Current-state wishlist user — terpisah dari BehaviorEvent.

    Menyimpan kondisi wishlist saat ini (bukan history); satu baris = produk yang sedang
    ada di wishlist. Saat user remove dari wishlist, baris ini dihapus.

    Attributes:
        user (ForeignKey): Pemilik wishlist.
        product (ForeignKey): Produk yang di-wishlist.
        created_at (DateTimeField): Kapan produk ditambahkan ke wishlist.
    """

    user    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_item')
        ]

    def __str__(self):
        """Return representasi ringkas berisi user_id dan product_id."""
        return f'Wishlist({self.user_id}, {self.product_id})'


# ── Serve layer (read-path — precomputed, disposable) ────────────────────────

class ProductSimilarity(models.Model):
    """F-28: top-K produk serupa per source product.

    Tabel ini bersifat disposable — di-truncate dan di-rebuild sepenuhnya
    setiap batch run ``compute_recommendations``. Score dihitung dari overlap
    atribut (series, timeline, grade) dengan bobot dari ``settings.SIMILARITY_WEIGHTS``.

    Attributes:
        source_product (ForeignKey): Produk referensi.
        target_product (ForeignKey): Produk yang mirip dengan source.
        score (FloatField): Skor kemiripan; semakin tinggi semakin mirip.
        computed_at (DateTimeField): Timestamp komputasi; auto-set saat INSERT.
    """

    source_product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='similar_to')
    target_product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='+')
    score          = models.FloatField()
    computed_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source_product', 'target_product'], name='unique_similarity_pair'
            )
        ]
        indexes = [
            models.Index(fields=['source_product', '-score']),
        ]


class UserRecommendation(models.Model):
    """F-29: top-N produk yang direkomendasikan untuk satu user.

    Tabel ini bersifat disposable — di-truncate dan di-rebuild sepenuhnya
    setiap batch run. Produk yang sudah dibeli user dikecualikan dari rekomendasi.

    Attributes:
        user (ForeignKey): User penerima rekomendasi.
        product (ForeignKey): Produk yang direkomendasikan.
        score (FloatField): Skor relevansi; semakin tinggi semakin relevan.
        reason (CharField): Dimensi terkuat penyumbang skor (contoh: ``Karena kamu menyukai seri ini``).
        computed_at (DateTimeField): Timestamp komputasi; auto-set saat INSERT.
    """

    user    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey('catalog.Product', on_delete=models.CASCADE, related_name='+')
    score   = models.FloatField()
    reason  = models.CharField(max_length=120, blank=True)
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_user_recommendation')
        ]
        indexes = [
            models.Index(fields=['user', '-score']),
        ]


class ProductPopularity(models.Model):
    """F-30: skor popularitas global per produk (cold-start fallback).

    OneToOne karena satu produk hanya punya satu baris popularitas. Digunakan
    sebagai fallback saat user belum punya cukup data (cold-start) atau untuk
    guest/anonymous user.

    Attributes:
        product (OneToOneField): Produk yang skornya disimpan.
        score (FloatField): Total weighted events (VIEW×1 + WISHLIST×3 + PURCHASE×5).
        computed_at (DateTimeField): Timestamp komputasi; auto-set saat INSERT.
    """

    product     = models.OneToOneField('catalog.Product', on_delete=models.CASCADE, related_name='popularity')
    score       = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-score'])]
