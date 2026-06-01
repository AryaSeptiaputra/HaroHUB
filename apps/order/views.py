"""View checkout, konfirmasi pembayaran, daftar pesanan, detail, dan pembatalan."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.models import Address
from apps.cart.models import Cart
from apps.common.exceptions import CheckoutError

from .models import Order, OrderStatus, PaymentMethod, ShippingRate
from .services import cancel_order as svc_cancel, checkout as svc_checkout, confirm_payment as svc_confirm


@login_required
def checkout_view(request):
    """Tampilkan form checkout dan proses pembuatan order.

    GET: Tampilkan form dengan daftar alamat user, pilihan metode pembayaran,
    dan preview ongkos kirim per kota. POST: Validasi input, panggil service
    ``checkout()``, redirect ke halaman pembayaran.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse:
            - Redirect ke ``cart:index`` jika cart kosong.
            - Redirect ke ``accounts:address_create`` jika tidak punya alamat.
            - Redirect ke ``order:payment`` jika POST berhasil.
            - Redirect ke form checkout jika validasi gagal.
            - Render ``order/checkout.html`` untuk GET.

    Raises:
        Http404: Jika Cart tidak ditemukan untuk user.
    """
    cart = get_object_or_404(Cart, user=request.user)

    if not cart.items.exists():
        messages.warning(request, 'Keranjang kamu kosong.')
        return redirect('cart:index')

    addresses = list(request.user.addresses.all().order_by('-is_default', 'recipient_name'))
    if not addresses:
        messages.info(request, 'Tambahkan alamat pengiriman terlebih dahulu.')
        return redirect('accounts:address_create')

    if request.method == 'POST':
        address_id     = request.POST.get('address_id')
        payment_method = request.POST.get('payment_method')

        try:
            address = request.user.addresses.get(pk=address_id)
        except Address.DoesNotExist:
            messages.error(request, 'Pilih alamat pengiriman yang valid.')
            return redirect('order:checkout')

        if payment_method not in [m[0] for m in PaymentMethod.choices]:
            messages.error(request, 'Pilih metode pembayaran.')
            return redirect('order:checkout')

        try:
            order = svc_checkout(cart, address, payment_method)
        except CheckoutError as exc:
            messages.error(request, str(exc))
            return redirect('order:checkout')

        return redirect('order:payment', order_number=order.order_number)

    # Buat peta kota → ongkir untuk preview
    rates = {r.city.lower(): r for r in ShippingRate.objects.filter(is_active=True)}
    items = list(
        cart.items
        .select_related('product__grade')
        .prefetch_related('product__images')
    )

    return render(request, 'order/checkout.html', {
        'cart': cart,
        'items': items,
        'addresses': addresses,
        'payment_methods': PaymentMethod.choices,
        'rates': rates,
        'available_cities': sorted(rates.keys()),
    })


@login_required
def payment_view(request, order_number):
    """Tampilkan halaman pembayaran dan proses konfirmasi (mock).

    Order yang sudah bukan PENDING di-redirect langsung ke detail. POST
    memicu ``confirm_payment()`` yang mengubah status Payment dan Order.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        order_number (str): Nomor order berformat ``HH-YYYYMMDD-XXXX``.

    Returns:
        HttpResponse:
            - Redirect ke ``order:detail`` jika order bukan PENDING.
            - Redirect ke ``order:detail`` setelah konfirmasi berhasil.
            - Render ``order/payment.html`` untuk GET.

    Raises:
        Http404: Jika order tidak ditemukan atau bukan milik request.user.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if order.status != OrderStatus.PENDING:
        return redirect('order:detail', order_number=order_number)

    payment = order.payment

    if request.method == 'POST':
        svc_confirm(payment)
        messages.success(request, f'Pembayaran dikonfirmasi! Pesanan {order.order_number} sedang diproses.')
        return redirect('order:detail', order_number=order_number)

    return render(request, 'order/payment.html', {'order': order, 'payment': payment})


@login_required
def order_list_view(request):
    """Tampilkan daftar semua pesanan milik user diurutkan terbaru.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.

    Returns:
        HttpResponse: Render ``order/list.html`` dengan konteks:
            - ``orders``: QuerySet Order user dengan prefetch items.
    """
    orders = request.user.orders.prefetch_related('items').order_by('-created_at')
    return render(request, 'order/list.html', {'orders': orders})


@login_required
def order_detail_view(request, order_number):
    """Tampilkan detail satu pesanan beserta item-itemnya.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        order_number (str): Nomor order berformat ``HH-YYYYMMDD-XXXX``.

    Returns:
        HttpResponse: Render ``order/detail.html`` dengan konteks:
            - ``order``: Instance Order.
            - ``items``: QuerySet OrderItem dengan relasi produk.

    Raises:
        Http404: Jika order tidak ditemukan atau bukan milik request.user.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.select_related('product')
    return render(request, 'order/detail.html', {'order': order, 'items': items})


@login_required
def cancel_order_view(request, order_number):
    """Tampilkan konfirmasi dan proses pembatalan pesanan oleh user.

    GET: Tampilkan halaman konfirmasi. POST: Panggil service ``cancel_order()``.
    Order yang tidak bisa dibatalkan (SHIPPED/COMPLETED) menampilkan pesan error.

    Args:
        request (HttpRequest): HTTP request objek; user harus terautentikasi.
        order_number (str): Nomor order berformat ``HH-YYYYMMDD-XXXX``.

    Returns:
        HttpResponse:
            - Redirect ke ``order:detail`` dengan error jika tidak bisa dibatalkan.
            - Redirect ke ``order:detail`` setelah berhasil dibatalkan.
            - Render ``order/cancel_confirm.html`` untuk GET.

    Raises:
        Http404: Jika order tidak ditemukan atau bukan milik request.user.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)

    if not order.is_cancellable:
        messages.error(request, 'Pesanan ini tidak dapat dibatalkan.')
        return redirect('order:detail', order_number=order_number)

    if request.method == 'POST':
        reason = request.POST.get('reason', 'Dibatalkan oleh pembeli.')
        svc_cancel(order, reason=reason)
        messages.success(request, f'Pesanan {order.order_number} berhasil dibatalkan.')
        return redirect('order:detail', order_number=order_number)

    return render(request, 'order/cancel_confirm.html', {'order': order})


def shipping_preview_view(request):
    """HTMX endpoint — kembalikan preview ongkir berdasarkan address_id yang dipilih.

    Tidak membutuhkan login; mengembalikan partial kosong jika user tidak login
    atau address_id tidak valid.

    Args:
        request (HttpRequest): HTTP request dengan query param:
            - ``address_id`` (str): Primary key Address yang dipilih di form checkout.

    Returns:
        HttpResponse: Render partial ``partials/_shipping_preview.html`` dengan konteks:
            - ``rate``: Instance ShippingRate untuk kota address, atau None jika tidak ditemukan.
    """
    rate = None
    if request.user.is_authenticated:
        address_id = request.GET.get('address_id', '')
        if address_id:
            try:
                address = request.user.addresses.get(pk=address_id)
                rate = ShippingRate.objects.filter(city__iexact=address.city, is_active=True).first()
            except Exception:
                pass
    return render(request, 'partials/_shipping_preview.html', {'rate': rate})
