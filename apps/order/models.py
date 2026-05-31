from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ALLOWED_TRANSITIONS = {}  # Diisi setelah class OrderStatus didefinisikan


class OrderStatus(models.TextChoices):
    PENDING    = 'PENDING',    'Menunggu Pembayaran'
    PAID       = 'PAID',       'Dibayar'
    PROCESSING = 'PROCESSING', 'Diproses'
    SHIPPED    = 'SHIPPED',    'Dikirim'
    COMPLETED  = 'COMPLETED',  'Selesai'
    CANCELLED  = 'CANCELLED',  'Dibatalkan'


ALLOWED_TRANSITIONS = {
    OrderStatus.PENDING:    {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID:       {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED:    {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED:  set(),
    OrderStatus.CANCELLED:  set(),
}


class PaymentMethod(models.TextChoices):
    BANK_TRANSFER = 'BANK_TRANSFER', 'Transfer Bank'
    E_WALLET      = 'E_WALLET',      'E-Wallet'
    QRIS          = 'QRIS',          'QRIS'
    COD           = 'COD',           'Bayar di Tempat'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Menunggu Pembayaran'
    PAID    = 'PAID',    'Lunas'
    FAILED  = 'FAILED',  'Gagal'
    EXPIRED = 'EXPIRED', 'Kedaluwarsa'


class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # Snapshot alamat — dibekukan saat checkout
    shipping_recipient_name = models.CharField(max_length=100)
    shipping_phone          = models.CharField(max_length=20)
    shipping_full_address   = models.TextField()
    shipping_city           = models.CharField(max_length=100)
    shipping_postal_code    = models.CharField(max_length=10)
    shipping_notes          = models.CharField(max_length=255, blank=True)

    # Snapshot finansial — dibekukan saat checkout
    subtotal      = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total         = models.DecimalField(max_digits=12, decimal_places=2)

    # Timestamps transisi
    shipped_at          = models.DateTimeField(null=True, blank=True)
    completed_at        = models.DateTimeField(null=True, blank=True)
    cancelled_at        = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number or f'Order #{self.pk}'

    # ── State machine ──────────────────────────────────────────────────────────

    def can_transition_to(self, new_status):
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status, reason=''):
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f'Transisi {self.get_status_display()} → {new_status} tidak diizinkan.'
            )
        self.status = new_status
        now = timezone.now()
        if new_status == OrderStatus.SHIPPED:
            self.shipped_at = now
        elif new_status == OrderStatus.COMPLETED:
            self.completed_at = now
        elif new_status == OrderStatus.CANCELLED:
            self.cancelled_at = now
            self.cancellation_reason = reason
        self.save()

    # ── Two-phase save untuk order_number ─────────────────────────────────────

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = f'HH-{self.created_at:%Y%m%d}-{self.id:04d}'
            super().save(update_fields=['order_number'])

    @property
    def is_cancellable(self):
        return self.can_transition_to(OrderStatus.CANCELLED)


class OrderItem(models.Model):
    order   = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('produk.Product', on_delete=models.PROTECT, related_name='order_items')

    # Snapshot — dibekukan saat order dibuat
    product_name      = models.CharField(max_length=200)
    product_image     = models.CharField(max_length=500, blank=True)
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)
    quantity          = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price_at_purchase * self.quantity

    def __str__(self):
        return f'{self.product_name} ×{self.quantity}'


class ShippingRate(models.Model):
    city           = models.CharField(max_length=100, unique=True)
    cost           = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_days = models.CharField(max_length=20, blank=True)
    is_active      = models.BooleanField(default=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city']

    def __str__(self):
        return f'{self.city} — Rp {self.cost:,.0f}'


class Payment(models.Model):
    order           = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method          = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status          = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_ref = models.CharField(max_length=64, blank=True)
    paid_at         = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment({self.order_id}, {self.status})'
