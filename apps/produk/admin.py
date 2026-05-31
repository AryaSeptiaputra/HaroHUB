from django.contrib import admin
from django.utils.html import format_html

from .models import Grade, Product, ProductImage, Series, Timeline


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'display_order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.image.url)
        return '—'
    preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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
    list_display = ('name', 'slug', 'scale')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Timeline)
class TimelineAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'timeline', 'slug')
    list_filter = ('timeline',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
