"""QuerySet dan Manager kustom untuk Product."""
from django.db import models


class ProductQuerySet(models.QuerySet):
    """QuerySet dengan method shortcut untuk filter produk yang umum dipakai."""

    def active(self):
        """Kembalikan produk yang bukan DISCONTINUED (ACTIVE dan PRE_ORDER).

        Returns:
            ProductQuerySet: QuerySet produk dengan status selain DISCONTINUED.
        """
        return self.exclude(status='DISCONTINUED')

    def for_listing(self):
        """Kembalikan produk aktif dengan relasi yang dibutuhkan halaman listing.

        Melakukan ``select_related`` grade dan series/timeline, serta
        ``prefetch_related`` images untuk menghindari N+1 query di template.

        Returns:
            ProductQuerySet: QuerySet produk aktif siap tampil di halaman listing.
        """
        return (self.active()
                .select_related('grade', 'series__timeline')
                .prefetch_related('images'))


class ProductManager(models.Manager):
    """Manager untuk Product yang menggunakan ``ProductQuerySet`` sebagai base QuerySet."""

    def get_queryset(self):
        """Return QuerySet berbasis ``ProductQuerySet``.

        Returns:
            ProductQuerySet: QuerySet dengan method shortcut tambahan.
        """
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        """Shortcut ke ``ProductQuerySet.active()``.

        Returns:
            ProductQuerySet: QuerySet produk bukan DISCONTINUED.
        """
        return self.get_queryset().active()

    def for_listing(self):
        """Shortcut ke ``ProductQuerySet.for_listing()``.

        Returns:
            ProductQuerySet: QuerySet produk aktif dengan relasi untuk listing.
        """
        return self.get_queryset().for_listing()
