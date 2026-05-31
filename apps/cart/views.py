from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from apps.produk.models import Product, ProductStatus

from .models import Cart, CartItem


def _get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def _items_qs(cart):
    return (cart.items
            .select_related('product__grade', 'product__series__timeline')
            .prefetch_related('product__images'))


def _htmx_cart_refresh(request, cart):
    """Kembalikan partial cart body + OOB badge untuk semua HTMX cart actions."""
    cart.refresh_from_db()
    items = list(_items_qs(cart))
    count = cart.item_count

    body_html = render_to_string(
        'partials/_cart_body.html',
        {'cart': cart, 'items': items},
        request=request,
    )
    badge_class = 'hidden' if count == 0 else 'bg-blue-600 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center'
    badge_html = (
        f'<span id="cart-badge" hx-swap-oob="true" class="{badge_class}">'
        f'{count}</span>'
    )
    return HttpResponse(body_html + badge_html)


@login_required
def cart_index(request):
    cart = _get_or_create_cart(request.user)
    items = list(_items_qs(cart))
    return render(request, 'cart/index.html', {'cart': cart, 'items': items})


@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('/')

    product = get_object_or_404(
        Product,
        pk=product_id,
        status__in=[ProductStatus.ACTIVE, ProductStatus.PRE_ORDER],
    )

    if product.status == ProductStatus.ACTIVE and product.stock == 0:
        messages.error(request, f'"{product.name}" sedang habis stok.')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    try:
        qty = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        qty = 1

    # Cap qty sebelum menyimpan — berlaku untuk create maupun update
    if product.status == ProductStatus.ACTIVE:
        qty = min(qty, product.stock)

    cart = _get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': qty},
    )
    if not created:
        new_qty = item.quantity + qty
        if product.status == ProductStatus.ACTIVE:
            new_qty = min(new_qty, product.stock)
        item.quantity = new_qty
        item.save(update_fields=['quantity'])

    messages.success(request, f'"{product.name}" ditambahkan ke keranjang.')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def update_item(request, item_id):
    if request.method != 'POST':
        return redirect('cart:index')

    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)

    try:
        qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        qty = 1

    cart = item.cart

    if qty <= 0:
        item.delete()
    else:
        if item.product.status == ProductStatus.ACTIVE and item.product.stock > 0:
            qty = min(qty, item.product.stock)
        item.quantity = max(1, qty)
        item.save(update_fields=['quantity'])

    if request.headers.get('HX-Request'):
        return _htmx_cart_refresh(request, cart)
    return redirect('cart:index')


@login_required
def remove_item(request, item_id):
    if request.method != 'POST':
        return redirect('cart:index')

    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart = item.cart
    item.delete()

    if request.headers.get('HX-Request'):
        return _htmx_cart_refresh(request, cart)

    messages.success(request, 'Item berhasil dihapus dari keranjang.')
    return redirect('cart:index')
