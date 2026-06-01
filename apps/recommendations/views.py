"""View HTMX untuk widget rekomendasi (serupa, untuk-kamu) dan toggle wishlist."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Product

from .services import (
    get_popular_products, get_similar_products,
    get_user_recommendations, toggle_wishlist,
)


def widget_similar(request, product_id):
    """F-28: HTMX partial — render widget Produk Serupa.

    Dipanggil dari halaman detail produk via HTMX untuk lazy-load widget
    serupa agar tidak memblokir render halaman utama.

    Args:
        request (HttpRequest): HTTP request objek.
        product_id (int): Primary key produk referensi.

    Returns:
        HttpResponse: Render partial ``partials/_widget_similar.html`` dengan konteks:
            - ``products``: List hingga 6 produk serupa.
            - ``source_product``: Instance produk referensi.

    Raises:
        Http404: Jika produk dengan ``product_id`` tidak ditemukan.
    """
    product  = get_object_or_404(Product, pk=product_id)
    products = get_similar_products(product, n=6)
    return render(request, 'partials/_widget_similar.html', {
        'products': products,
        'source_product': product,
    })


def widget_for_you(request):
    """F-29 + F-30: HTMX partial — render widget Untuk Kamu atau Produk Populer.

    User terautentikasi mendapat rekomendasi personal (F-29) atau fallback
    popularitas (F-30). Guest mendapat produk terpopuler langsung.

    Args:
        request (HttpRequest): HTTP request objek.

    Returns:
        HttpResponse: Render partial ``partials/_widget_for_you.html`` dengan konteks:
            - ``products``: List hingga 8 produk rekomendasi.
            - ``source``: String ``'personalized'`` atau ``'popular'``.
    """
    if request.user.is_authenticated:
        products, source = get_user_recommendations(request.user, n=8)
    else:
        products = get_popular_products(n=8)
        source   = 'popular'
    return render(request, 'partials/_widget_for_you.html', {
        'products': products,
        'source': source,
    })


@login_required
def wishlist_toggle(request, product_id):
    """Toggle wishlist produk dan emit WISHLIST event ke recommendation engine.

    Hanya menerima POST. Response bergantung pada jenis request:
    - HTMX: kembalikan partial button wishlist yang di-update.
    - Non-HTMX: redirect ke halaman sebelumnya atau root.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        product_id (int): Primary key produk yang akan di-toggle wishlist-nya.

    Returns:
        HttpResponse:
            - Redirect ke root jika bukan POST.
            - Render partial ``partials/_wishlist_btn.html`` jika HTMX request.
            - Redirect ke ``HTTP_REFERER`` atau root jika non-HTMX.

    Raises:
        Http404: Jika produk dengan ``product_id`` tidak ditemukan.
    """
    if request.method != 'POST':
        return redirect('/')

    product      = get_object_or_404(Product, pk=product_id)
    is_wishlisted = toggle_wishlist(request.user, product)

    if request.headers.get('HX-Request'):
        return render(request, 'partials/_wishlist_btn.html', {
            'product': product,
            'is_wishlisted': is_wishlisted,
        })
    return redirect(request.META.get('HTTP_REFERER', '/'))
