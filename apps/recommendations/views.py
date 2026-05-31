from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.catalog.models import Product

from .services import (
    get_popular_products, get_similar_products,
    get_user_recommendations, toggle_wishlist,
)


def widget_similar(request, product_id):
    """F-28: HTMX partial — Produk Serupa."""
    product  = get_object_or_404(Product, pk=product_id)
    products = get_similar_products(product, n=6)
    return render(request, 'partials/_widget_similar.html', {
        'products': products,
        'source_product': product,
    })


def widget_for_you(request):
    """F-29 + F-30: HTMX partial — Untuk Kamu / Populer."""
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
    """Toggle wishlist + emit WISHLIST event."""
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
