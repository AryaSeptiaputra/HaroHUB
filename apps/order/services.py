from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import CheckoutError
from apps.common.generators import generate_mock_transaction_ref

from .models import Order, OrderItem, OrderStatus, Payment, PaymentStatus, ShippingRate


@transaction.atomic
def checkout(cart, address, payment_method):
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
    payment.status          = PaymentStatus.PAID
    payment.paid_at         = timezone.now()
    payment.transaction_ref = transaction_ref or generate_mock_transaction_ref()
    payment.save()
    payment.order.transition_to(OrderStatus.PAID)

    # Emit PURCHASE event ke recommendation engine
    from apps.rekomendasi.services import record_event
    for item in payment.order.items.select_related('product'):
        record_event(payment.order.user, item.product, 'PURCHASE')


@transaction.atomic
def expire_payment(payment):
    payment.status = PaymentStatus.EXPIRED
    payment.save()
    cancel_order(payment.order, reason='Pembayaran kedaluwarsa.')


@transaction.atomic
def cancel_order(order, reason=''):
    order.transition_to(OrderStatus.CANCELLED, reason=reason)
    # Kembalikan stok untuk produk ACTIVE
    for item in order.items.select_related('product'):
        if item.product.status == 'ACTIVE':
            item.product.__class__.objects.filter(pk=item.product.pk).update(
                stock=item.product.stock + item.quantity
            )
