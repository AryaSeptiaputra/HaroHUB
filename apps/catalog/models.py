"""Model produk Gunpla: Timeline, Series, Grade, Product, dan ProductImage."""
from django.db import models

from apps.core.models import TimeStampedModel
from .managers import ProductManager


class Timeline(models.Model):
    """Universe Gundam (misalnya Universal Century, Cosmic Era).

    Timeline adalah level tertinggi dalam hierarki: Timeline → Series → Product.

    Attributes:
        slug (SlugField): Identifier URL-safe unik (contoh: ``uc``, ``ce``).
        name (CharField): Nama tampilan (contoh: ``Universal Century``).
        description (TextField): Deskripsi singkat universe; opsional.
    """

    slug = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return nama timeline."""
        return self.name


class Series(models.Model):
    """Serial Gundam di dalam satu Timeline (contoh: Gundam SEED di bawah Cosmic Era).

    Attributes:
        slug (SlugField): Identifier URL-safe unik.
        name (CharField): Nama serial.
        timeline (ForeignKey): Timeline induk; PROTECT mencegah hapus jika masih ada series.
    """

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    timeline = models.ForeignKey(Timeline, on_delete=models.PROTECT, related_name='series')

    class Meta:
        verbose_name_plural = 'series'
        ordering = ['name']

    def __str__(self):
        """Return nama serial."""
        return self.name


class Grade(models.Model):
    """Grade (tingkat detail) kit Gunpla (contoh: HG, MG, RG, PG).

    Attributes:
        slug (SlugField): Identifier URL-safe unik (contoh: ``hg``, ``mg``).
        name (CharField): Nama grade (contoh: ``High Grade``).
        scale (CharField): Skala umum untuk grade ini (contoh: ``1/144``); opsional.
        description (TextField): Deskripsi singkat grade; opsional.
    """

    slug = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    scale = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        """Return nama grade."""
        return self.name


class ProductStatus(models.TextChoices):
    """Status ketersediaan produk di toko."""

    ACTIVE = 'ACTIVE', 'Active'
    PRE_ORDER = 'PRE_ORDER', 'Pre-order'
    DISCONTINUED = 'DISCONTINUED', 'Discontinued'


class ProductCondition(models.TextChoices):
    """Kondisi fisik produk."""

    SEALED = 'SEALED', 'Sealed'
    PRE_OWNED = 'PRE_OWNED', 'Pre-owned'


class Product(TimeStampedModel):
    """Produk Gunpla yang dijual di HaroHUB.

    ``timeline`` tidak disimpan langsung pada model — diturunkan melalui ``series.timeline``
    untuk memastikan konsistensi hierarki data.

    Attributes:
        name (CharField): Nama lengkap produk.
        slug (SlugField): Identifier URL-safe unik.
        description (TextField): Deskripsi produk; opsional.
        price (DecimalField): Harga satuan dalam Rupiah.
        stock (PositiveIntegerField): Jumlah stok tersedia.
        grade (ForeignKey): Grade kit; PROTECT mencegah hapus grade yang masih dipakai.
        series (ForeignKey): Serial induk; timeline diambil dari sini.
        status (CharField): Status produk (``ACTIVE`` | ``PRE_ORDER`` | ``DISCONTINUED``).
        condition (CharField): Kondisi produk (``SEALED`` | ``PRE_OWNED``).
        objects (ProductManager): Manager dengan shortcut ``active()`` dan ``for_listing()``.
    """

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name='products')
    # timeline tidak disimpan langsung — diturunkan via series.timeline
    series = models.ForeignKey(Series, on_delete=models.PROTECT, related_name='products')

    status = models.CharField(
        max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE
    )
    condition = models.CharField(
        max_length=20, choices=ProductCondition.choices, default=ProductCondition.SEALED
    )

    objects = ProductManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """Return nama produk."""
        return self.name

    @property
    def timeline(self):
        """Timeline produk, diturunkan dari ``series.timeline``.

        Returns:
            Timeline: Instance Timeline induk series produk ini.
        """
        return self.series.timeline

    @property
    def primary_image(self):
        """Gambar utama produk (``is_primary=True``), atau ``None`` jika tidak ada.

        Returns:
            ProductImage | None: Instance gambar utama, atau None.
        """
        return self.images.filter(is_primary=True).first()

    @property
    def is_available(self):
        """Cek apakah produk bisa dibeli (ACTIVE atau PRE_ORDER).

        Returns:
            bool: True jika status ACTIVE atau PRE_ORDER.
        """
        return self.status in (ProductStatus.ACTIVE, ProductStatus.PRE_ORDER)


class ProductImage(models.Model):
    """Gambar produk; satu produk bisa punya banyak gambar, satu ditandai sebagai primary.

    Constraint database memastikan hanya ada satu ``is_primary=True`` per produk.

    Attributes:
        product (ForeignKey): Produk pemilik gambar; CASCADE saat produk dihapus.
        image (ImageField): File gambar; di-upload ke direktori ``products/``.
        alt_text (CharField): Teks alternatif untuk aksesibilitas; opsional.
        is_primary (BooleanField): Tandai sebagai gambar utama produk.
        display_order (PositiveIntegerField): Urutan tampil di galeri.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']
        constraints = [
            models.UniqueConstraint(
                fields=['product'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_product',
            )
        ]

    def __str__(self):
        """Return nama produk dan keterangan posisi gambar."""
        return f'{self.product.name} — {"primary" if self.is_primary else f"#{self.display_order}"}'
