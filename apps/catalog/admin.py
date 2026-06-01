"""Registrasi admin untuk Product (dengan inline image), Grade, Timeline, dan Series."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Grade, Product, ProductImage, Series, Timeline


class ProductImageInline(admin.TabularInline):
    """Inline tabular untuk mengelola gambar produk langsung di halaman Product."""

    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'display_order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        """Render thumbnail gambar produk di kolom preview.

        Args:
            obj (ProductImage): Instance gambar yang sedang ditampilkan.

        Returns:
            str: Tag HTML ``<img>`` dengan thumbnail, atau tanda '—' jika belum ada gambar.
        """
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.image.url)
        return '—'
    preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin untuk Product dengan list editable status/stok, filter lengkap, dan inline gambar."""

    list_display = ('name', 'grade', 'series', 'price', 'stock', 'status', 'condition', 'created_at')
    list_filter = ('status', 'condition', 'grade', 'series__timeline')
    search_fields = ('name', 'description', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ('grade', 'series')
    inlines = [ProductImageInline]
    list_editable = ('status', 'stock')
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description'),
        }),
        ('Klasifikasi', {
            'fields': ('grade', 'series'),
        }),
        ('Harga & Stok', {
            'fields': ('price', 'stock'),
        }),
        ('Status', {
            'fields': ('status', 'condition'),
        }),
    )


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """Admin untuk Grade dengan auto-populate slug dari name."""

    list_display = ('name', 'slug', 'scale')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    """Admin untuk Timeline dengan auto-populate slug dari name."""

    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    """Admin untuk Series dengan filter timeline dan auto-populate slug dari name."""

    list_display = ('name', 'timeline', 'slug')
    list_filter = ('timeline',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
