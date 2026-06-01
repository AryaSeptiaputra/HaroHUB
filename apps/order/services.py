"""Service layer order: checkout atomik, konfirmasi pembayaran, dan pembatalan dengan restock."""
from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import CheckoutError
from apps.common.generators import generate_mock_transaction_ref

from .models import Order, OrderItem, OrderStatus, Payment, PaymentStatus, ShippingRate


@transaction.atomic
def checkout(cart, address, payment_method):
    """Proses checkout: validasi, buat Order + OrderItem + Payment, kurangi stok, kosongkan cart.

    Seluruh operasi dijalankan dalam satu transaksi atomik. Jika salah satu
    validasi gagal atau terjadi error, semua perubahan di-rollback.

    Args:
        cart (Cart): Keranjang belanja yang akan di-checkout; harus punya minimal satu item.
        address (Address): Alamat pengiriman yang dipilih user; kota digunakan untuk lookup ongkir.
        payment_method (str): Salah satu nilai dari ``PaymentMethod.choices``.

    Returns:
        Order: Instance Order baru dengan status PENDING dan order_number yang sudah di-generate.

    Raises:
        CheckoutError: Jika cart kosong, ada produk DISCONTINUED, stok tidak mencukupi,
            atau kota address tidak ada di tabel ShippingRate.
    """
    items = list(cart.items.select_related('product').prefetch_related('product__images'))
    if not items:
        raise CheckoutError('Keranjang kosong.')

    for item in items:
        if item.product.status == 'DISCONTINUED':
            raise CheckoutError(f'"{item.product.name}" sudah tidak tersedia.')
        if item.product.status == 'ACTIVE' and item.product.stock < item.quantity:
            raise CheckoutError(
                f'Stok "{item.product.name}" tidak mencukupi '
                f'(tersedia: {item.product.stock}, diminta: {item.quantity}).'
            )

    try:
        rate = ShippingRate.objects.get(city__iexact=address.city, is_active=True)
    except ShippingRate.DoesNotExist:
        raise CheckoutError(
            f'Ongkos kirim ke "{address.city}" belum tersedia. '
            'Pilih kota dari daftar yang tersedia.'
        )

    subtotal      = sum(item.subtotal for item in items)
    shipping_cost = rate.cost
    total         = subtotal + shipping_cost

    order = Order.objects.create(
        user                    = cart.user,
        shipping_recipient_name = address.recipient_name,
        shipping_phone          = address.phone,
        shipping_full_address   = address.full_address,
        shipping_city           = address.city,
        shipping_postal_code    = address.postal_code,
        shipping_notes          = address.notes,
        subtotal                = subtotal,
        shipping_cost           = shipping_cost,
        total                   = total,
    )

    order_items = []
    for item in items:
        primary = item.product.images.filter(is_primary=True).first()
        order_items.append(OrderItem(
            order             = order,
            product           = item.product,
            product_name      = item.product.name,
            product_image     = primary.image.url if primary else '',
            price_at_purchase = item.product.price,
            quantity          = item.quantity,
        ))
    OrderItem.objects.bulk_create(order_items)

    # Decrement stock untuk produk ACTIVE
    for item in items:
        if item.product.status == 'ACTIVE':
            item.product.__class__.objects.filter(pk=item.product.pk).update(
                stock=item.product.stock - item.quantity
            )

    Payment.objects.create(order=order, method=payment_method, amount=total)

    cart.items.all().delete()

    return order


@transaction.atomic
def confirm_payment(payment, transaction_ref=''):
    """Konfirmasi pembayaran: set Payment.status=PAID dan transisi Order ke PAID.

    Setelah payment terkonfirmasi, emit event PURCHASE ke recommendation engine
    untuk setiap item dalam order.

    Args:
        payment (Payment): Instance Payment yang akan dikonfirmasi.
        transaction_ref (str, optional): Referensi transaksi dari gateway.
            Jika kosong, akan di-generate otomatis sebagai mock reference.
    """
    payment.status          = PaymentStatus.PAID
    payment.paid_at         = timezone.now()
    payment.transaction_ref = transaction_ref or generate_mock_transaction_ref()
    payment.save()
    payment.order.transition_to(OrderStatus.PAID)

    # Emit PURCHASE event ke recommendation engine
    from apps.recommendations.services import record_event
    for item in payment.order.items.select_related('product'):
        record_event(payment.order.user, item.product, 'PURCHASE')


@transaction.atomic
def expire_payment(payment):
    """Tandai pembayaran sebagai EXPIRED dan batalkan order terkait.

    Args:
        payment (Payment): Instance Payment yang kedaluwarsa.
    """
    payment.status = PaymentStatus.EXPIRED
    payment.save()
    cancel_order(payment.order, reason='Pembayaran kedaluwarsa.')


@transaction.atomic
def cancel_order(order, reason=''):
    """Batalkan order dan kembalikan stok produk ACTIVE ke nilai semula.

    Args:
        order (Order): Instance Order yang akan dibatalkan.
        reason (str, optional): Alasan pembatalan yang disimpan di ``order.cancellation_reason``.

    Raises:
        ValidationError: Jika transisi ke CANCELLED tidak diizinkan dari status saat ini
            (diteruskan dari ``Order.transition_to``).
    """
    order.transition_to(OrderStatus.CANCELLED, reason=reason)
    # Kembalikan stok untuk produk ACTIVE
    for item in order.items.select_related('product'):
        if item.product.status == 'ACTIVE':
            item.product.__class__.objects.filter(pk=item.product.pk).update(
                stock=item.product.stock + item.quantity
            )
