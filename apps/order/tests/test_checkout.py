from django.test import TestCase

from apps.accounts.models import Address, User
from apps.cart.models import Cart, CartItem
from apps.common.exceptions import CheckoutError
from apps.order.models import Order, OrderStatus, PaymentMethod, PaymentStatus, ShippingRate
from apps.order.services import cancel_order, checkout, confirm_payment
from apps.produk.models import Grade, Product, Series, Timeline


def make_user(email='buyer@t.id'):
    return User.objects.create_user(email=email, password='pass')


def make_address(user, city='Jakarta'):
    return Address.objects.create(
        user=user, recipient_name='Test', phone='08x',
        full_address='Jl. Test', city=city, postal_code='10000',
    )


def make_product(name='Kit', stock=10, status='ACTIVE', price=100000):
    tl, _ = Timeline.objects.get_or_create(slug='uc', defaults={'name': 'UC'})
    sr, _ = Series.objects.get_or_create(slug='sr', defaults={'name': 'SR', 'timeline': tl})
    gr, _ = Grade.objects.get_or_create(slug='hg', defaults={'name': 'HG', 'scale': '1/144'})
    return Product.objects.get_or_create(
        slug=name.lower(),
        defaults={'name': name, 'grade': gr, 'series': sr, 'price': price, 'stock': stock, 'status': status},
    )[0]


def make_rate(city='Jakarta', cost=15000):
    return ShippingRate.objects.get_or_create(city=city, defaults={'cost': cost, 'estimated_days': '1-2'})[0]


class CheckoutServiceTest(TestCase):
    def setUp(self):
        self.user    = make_user()
        self.address = make_address(self.user)
        self.product = make_product()
        self.rate    = make_rate()
        self.cart    = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_happy_path_creates_order(self):
        order = checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.assertIsNotNone(order.order_number)
        self.assertEqual(order.status, OrderStatus.PENDING)
        self.assertEqual(order.items.count(), 1)

    def test_snapshots_price(self):
        order = checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        item = order.items.first()
        self.assertEqual(item.price_at_purchase, self.product.price)
        self.assertEqual(item.quantity, 2)

    def test_snapshots_address(self):
        order = checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.assertEqual(order.shipping_city, self.address.city)
        self.assertEqual(order.shipping_recipient_name, self.address.recipient_name)

    def test_decrements_stock(self):
        checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_clears_cart(self):
        checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.assertEqual(self.cart.items.count(), 0)

    def test_creates_payment(self):
        order = checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.assertTrue(hasattr(order, 'payment'))
        self.assertEqual(order.payment.status, PaymentStatus.PENDING)

    def test_shipping_cost_added(self):
        order = checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)
        self.assertEqual(order.shipping_cost, self.rate.cost)
        self.assertEqual(order.total, order.subtotal + self.rate.cost)

    def test_empty_cart_raises(self):
        self.cart.items.all().delete()
        with self.assertRaises(CheckoutError):
            checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)

    def test_insufficient_stock_raises(self):
        self.product.stock = 1
        self.product.save()
        with self.assertRaises(CheckoutError):
            checkout(self.cart, self.address, PaymentMethod.BANK_TRANSFER)

    def test_no_shipping_rate_raises(self):
        addr = make_address(self.user, city='Kota Tidak Ada')
        with self.assertRaises(CheckoutError):
            checkout(self.cart, addr, PaymentMethod.BANK_TRANSFER)


class ConfirmPaymentTest(TestCase):
    def setUp(self):
        user    = make_user('c@t.id')
        address = make_address(user)
        product = make_product('ConfirmKit')
        make_rate()
        cart    = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)
        self.order = checkout(cart, address, PaymentMethod.QRIS)

    def test_confirm_sets_paid(self):
        confirm_payment(self.order.payment)
        self.order.payment.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment.status, PaymentStatus.PAID)
        self.assertEqual(self.order.status, OrderStatus.PAID)
        self.assertIsNotNone(self.order.payment.paid_at)

    def test_transaction_ref_generated(self):
        confirm_payment(self.order.payment)
        self.order.payment.refresh_from_db()
        self.assertTrue(self.order.payment.transaction_ref.startswith('MOCK-'))


class CancelOrderTest(TestCase):
    def setUp(self):
        user    = make_user('cancel@t.id')
        address = make_address(user)
        self.product = make_product('CancelKit', stock=5)
        make_rate()
        cart    = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.order = checkout(cart, address, PaymentMethod.COD)

    def test_cancel_restores_stock(self):
        self.product.refresh_from_db()
        stock_after_checkout = self.product.stock  # 5 - 2 = 3
        cancel_order(self.order, reason='Test cancel')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock_after_checkout + 2)

    def test_cancel_sets_status(self):
        cancel_order(self.order)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.CANCELLED)
