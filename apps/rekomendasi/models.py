from django.db import models


class EventType(models.TextChoices):
    VIEW     = 'VIEW',     'View'
    WISHLIST = 'WISHLIST', 'Wishlist'
    PURCHASE = 'PURCHASE', 'Purchase'


# ── Capture layer (write-path) ────────────────────────────────────────────────

class BehaviorEvent(models.Model):
    """Append-only event log. Tidak ada UPDATE/DELETE (kecuali pruning lama)."""
    user       = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='behavior_events')
    product    = models.ForeignKey('produk.Product', on_delete=models.CASCADE, related_name='behavior_events')
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),                   # F-29: agregasi per-user
            models.Index(fields=['product', 'event_type']),  # F-30: popularitas per produk
        ]

    def __str__(self):
        return f'{self.event_type}({self.user_id}, {self.product_id})'


class Wishlist(models.Model):
    """Current-state wishlist — terpisah dari event log."""
    user    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('produk.Product', on_delete=models.CASCADE, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_item')
        ]

    def __str__(self):
        return f'Wishlist({self.user_id}, {self.product_id})'


# ── Serve layer (read-path — precomputed, disposable) ────────────────────────

class ProductSimilarity(models.Model):
    """F-28: top-K produk serupa per source. Dibangun ulang tiap batch run."""
    source_product = models.ForeignKey('produk.Product', on_delete=models.CASCADE, related_name='similar_to')
    target_product = models.ForeignKey('produk.Product', on_delete=models.CASCADE, related_name='+')
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
    """F-29: top-N produk per user. Dibangun ulang tiap batch run."""
    user    = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='recommendations')
    product = models.ForeignKey('produk.Product', on_delete=models.CASCADE, related_name='+')
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
    """F-30: skor popularitas global. OneToOne karena satu baris per produk."""
    product     = models.OneToOneField('produk.Product', on_delete=models.CASCADE, related_name='popularity')
    score       = models.FloatField()
    computed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['-score'])]
