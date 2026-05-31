from django.db import models

from apps.core.models import TimeStampedModel
from .managers import ProductManager


class Timeline(models.Model):
    slug = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Series(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    timeline = models.ForeignKey(Timeline, on_delete=models.PROTECT, related_name='series')

    class Meta:
        verbose_name_plural = 'series'
        ordering = ['name']

    def __str__(self):
        return self.name


class Grade(models.Model):
    slug = models.SlugField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    scale = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PRE_ORDER = 'PRE_ORDER', 'Pre-order'
    DISCONTINUED = 'DISCONTINUED', 'Discontinued'


class ProductCondition(models.TextChoices):
    SEALED = 'SEALED', 'Sealed'
    PRE_OWNED = 'PRE_OWNED', 'Pre-owned'


class Product(TimeStampedModel):
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
        return self.name

    @property
    def timeline(self):
        return self.series.timeline

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()

    @property
    def is_available(self):
        return self.status in (ProductStatus.ACTIVE, ProductStatus.PRE_ORDER)


class ProductImage(models.Model):
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
        return f'{self.product.name} — {"primary" if self.is_primary else f"#{self.display_order}"}'
