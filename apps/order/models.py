"""Model Order (state machine), OrderItem (snapshot harga), ShippingRate, dan Payment."""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


ALLOWED_TRANSITIONS = {}  # Diisi setelah class OrderStatus didefinisikan


class OrderStatus(models.TextChoices):
    """Status alur pesanan dalam state machine."""

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
    """Metode pembayaran yang didukung (mock simulation, bukan gateway nyata)."""

    BANK_TRANSFER = 'BANK_TRANSFER', 'Transfer Bank'
    E_WALLET      = 'E_WALLET',      'E-Wallet'
    QRIS          = 'QRIS',          'QRIS'
    COD           = 'COD',           'Bayar di Tempat'


class PaymentStatus(models.TextChoices):
    """Status pembayaran untuk satu Order."""

    PENDING = 'PENDING', 'Menunggu Pembayaran'
    PAID    = 'PAID',    'Lunas'
    FAILED  = 'FAILED',  'Gagal'
    EXPIRED = 'EXPIRED', 'Kedaluwarsa'


class Order(models.Model):
    """Pesanan yang dibuat saat checkout; memiliki state machine untuk transisi status.

    Data alamat dan finansial di-snapshot saat checkout sehingga perubahan Address
    atau harga produk di kemudian hari tidak mempengaruhi pesanan yang sudah dibuat.

    ``order_number`` dibuat dalam dua tahap save karena membutuhkan ``id`` dari
    database dan timestamp ``created_at``.

    Attributes:
        order_number (CharField): Nomor pesanan unik berformat ``HH-YYYYMMDD-XXXX``.
        user (ForeignKey): User pemilik pesanan; PROTECT mencegah hapus user yang punya order.
        status (CharField): Status saat ini dari state machine.
        shipping_* (CharField/TextField): Snapshot alamat pengiriman saat checkout.
        subtotal (DecimalField): Total harga item sebelum ongkir (snapshot).
        shipping_cost (DecimalField): Ongkos kirim (snapshot).
        total (DecimalField): ``subtotal + shipping_cost`` (snapshot).
        shipped_at (DateTimeField): Timestamp transisi ke SHIPPED; None sebelumnya.
        completed_at (DateTimeField): Timestamp transisi ke COMPLETED; None sebelumnya.
        cancelled_at (DateTimeField): Timestamp transisi ke CANCELLED; None sebelumnya.
        cancellation_reason (CharField): Alasan pembatalan; opsional.
    """

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
        """Return order_number atau fallback ``Order #<pk>``."""
        return self.order_number or f'Order #{self.pk}'

    # ── State machine ──────────────────────────────────────────────────────────

    def can_transition_to(self, new_status):
        """Cek apakah transisi ke status baru diizinkan dari status saat ini.

        Args:
            new_status (str): Status tujuan yang akan dicek (nilai dari ``OrderStatus``).

        Returns:
            bool: True jika transisi valid sesuai ``ALLOWED_TRANSITIONS``.
        """
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status, reason=''):
        """Jalankan transisi status dan simpan timestamp yang relevan.

        Selalu panggil method ini (jangan set ``status`` langsung) agar
        validasi dan timestamp otomatis terjaga.

        Args:
            new_status (str): Status tujuan (nilai dari ``OrderStatus``).
            reason (str, optional): Alasan pembatalan; hanya dipakai saat ke CANCELLED.

        Raises:
            ValidationError: Jika transisi dari status saat ini ke ``new_status`` tidak diizinkan.
        """
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
        """Override save untuk generate ``order_number`` setelah ``id`` tersedia.

        ``order_number`` dibuat pada save kedua karena membutuhkan ``id`` dan ``created_at``
        yang baru tersedia setelah INSERT pertama ke database.

        Args:
            *args: Diteruskan ke ``super().save()``.
            **kwargs: Diteruskan ke ``super().save()``.
        """
        super().save(*args, **kwargs)
        if not self.order_number:
            self.order_number = f'HH-{self.created_at:%Y%m%d}-{self.id:04d}'
            super().save(update_fields=['order_number'])

    @property
    def is_cancellable(self):
        """Cek apakah pesanan masih bisa dibatalkan.

        Returns:
            bool: True jika transisi ke CANCELLED diizinkan dari status saat ini.
        """
        return self.can_transition_to(OrderStatus.CANCELLED)


class OrderItem(models.Model):
    """Satu baris item dalam Order dengan snapshot data produk saat pembelian.

    Harga, nama, dan URL gambar di-freeze saat checkout sehingga perubahan
    produk di kemudian hari tidak mengubah riwayat pesanan.

    Attributes:
        order (ForeignKey): Order induk; CASCADE saat order dihapus.
        product (ForeignKey): Referensi ke produk asli; PROTECT agar produk tidak terhapus.
        product_name (CharField): Snapshot nama produk saat checkout.
        product_image (CharField): Snapshot URL gambar utama saat checkout.
        price_at_purchase (DecimalField): Snapshot harga satuan saat checkout.
        quantity (PositiveIntegerField): Jumlah item yang dibeli.
    """

    order   = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.Product', on_delete=models.PROTECT, related_name='order_items')

    # Snapshot — dibekukan saat order dibuat
    product_name      = models.CharField(max_length=200)
    product_image     = models.CharField(max_length=500, blank=True)
    price_at_purchase = models.DecimalField(max_digits=12, decimal_places=2)
    quantity          = models.PositiveIntegerField()

    @property
    def subtotal(self):
        """Total harga item ini berdasarkan harga snapshot × quantity.

        Returns:
            Decimal: Hasil perkalian ``price_at_purchase`` × ``quantity``.
        """
        return self.price_at_purchase * self.quantity

    def __str__(self):
        """Return nama produk dan quantity."""
        return f'{self.product_name} ×{self.quantity}'


class ShippingRate(models.Model):
    """Ongkos kirim flat-rate per kota (mock, bukan integrasi RajaOngkir).

    Satu baris = satu kota. Lookup dilakukan dengan ``city__iexact`` di service layer.

    Attributes:
        city (CharField): Nama kota unik; case-insensitive saat lookup.
        cost (DecimalField): Ongkos kirim dalam Rupiah.
        estimated_days (CharField): Estimasi hari pengiriman (contoh: ``2-3``).
        is_active (BooleanField): Nonaktifkan kota tanpa menghapus data.
        updated_at (DateTimeField): Timestamp terakhir diperbarui.
    """

    city           = models.CharField(max_length=100, unique=True)
    cost           = models.DecimalField(max_digits=12, decimal_places=2)
    estimated_days = models.CharField(max_length=20, blank=True)
    is_active      = models.BooleanField(default=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city']

    def __str__(self):
        """Return nama kota dan biaya dalam format Rupiah."""
        return f'{self.city} — Rp {self.cost:,.0f}'


class Payment(models.Model):
    """Satu pembayaran yang terhubung one-to-one dengan Order.

    ``Payment.status = PAID`` adalah satu-satunya trigger untuk transisi
    ``Order PENDING → PAID`` — tidak ada cara lain yang valid.

    Attributes:
        order (OneToOneField): Order yang dibayar; CASCADE saat order dihapus.
        method (CharField): Metode pembayaran yang dipilih saat checkout.
        status (CharField): Status pembayaran saat ini.
        amount (DecimalField): Jumlah yang harus dibayar (sama dengan ``order.total``).
        transaction_ref (CharField): Referensi transaksi dari gateway; kosong jika mock.
        paid_at (DateTimeField): Timestamp konfirmasi pembayaran; None sebelum terkonfirmasi.
        created_at (DateTimeField): Timestamp payment dibuat.
    """

    order           = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method          = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status          = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    amount          = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_ref = models.CharField(max_length=64, blank=True)
    paid_at         = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return representasi string berisi order_id dan status pembayaran."""
        return f'Payment({self.order_id}, {self.status})'
