from django.test import TestCase

from apps.accounts.models import Address, User
from apps.cart.models import Cart, CartItem
from apps.order.models import Order, OrderStatus, PaymentMethod, ShippingRate
from apps.order.services import checkout
from apps.produk.models import Grade, Product, Series, Timeline


def setup_world(email='v@t.id'):
    user = User.objects.create_user(email=email, password='Pass123!')
    tl, _ = Timeline.objects.get_or_create(slug='uc2', defaults={'name': 'UC'})
    sr, _ = Series.objects.get_or_create(slug='sr2', defaults={'name': 'SR', 'timeline': tl})
    gr, _ = Grade.objects.get_or_create(slug='hg2', defaults={'name': 'HG', 'scale': '1/144'})
    product = Product.objects.create(slug='test-kit-v', name='Test Kit V', grade=gr, series=sr, price=100000, stock=10)
    ShippingRate.objects.get_or_create(city='Jakarta', defaults={'cost': 15000, 'estimated_days': '1-2'})
    address = Address.objects.create(
        user=user, recipient_name='Test', phone='08x',
        full_address='Jl.', city='Jakarta', postal_code='10000', is_default=True,
    )
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, product=product, quantity=1)
    return user, cart, address, product


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.user, self.cart, self.address, self.product = setup_world()
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        r = self.client.get('/order/checkout/')
        self.assertEqual(r.status_code, 302)

    def test_get_ok(self):
        r = self.client.get('/order/checkout/')
        self.assertEqual(r.status_code, 200)

    def test_empty_cart_redirects(self):
        self.cart.items.all().delete()
        r = self.client.get('/order/checkout/')
        self.assertRedirects(r, '/cart/', fetch_redirect_response=False)

    def test_no_address_redirects(self):
        self.address.delete()
        r = self.client.get('/order/checkout/')
        self.assertRedirects(r, '/accounts/addresses/add/', fetch_redirect_response=False)

    def test_post_creates_order_and_redirects_to_payment(self):
        r = self.client.post('/order/checkout/', {
            'address_id': self.address.pk,
            'payment_method': 'BANK_TRANSFER',
        })
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertRedirects(r, f'/order/{order.order_number}/payment/', fetch_redirect_response=False)

    def test_post_invalid_address_stays(self):
        r = self.client.post('/order/checkout/', {
            'address_id': 9999,
            'payment_method': 'BANK_TRANSFER',
        })
        self.assertRedirects(r, '/order/checkout/', fetch_redirect_response=False)


class PaymentViewTest(TestCase):
    def setUp(self):
        user, cart, address, _ = setup_world('p@t.id')
        self.client.force_login(user)
        self.order = checkout(cart, address, PaymentMethod.QRIS)

    def test_get_ok(self):
        r = self.client.get(f'/order/{self.order.order_number}/payment/')
        self.assertEqual(r.status_code, 200)

    def test_post_confirms_payment(self):
        r = self.client.post(f'/order/{self.order.order_number}/payment/')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.PAID)
        self.assertRedirects(r, f'/order/{self.order.order_number}/', fetch_redirect_response=False)

    def test_paid_order_redirects_to_detail(self):
        self.client.post(f'/order/{self.order.order_number}/payment/')
        r = self.client.get(f'/order/{self.order.order_number}/payment/')
        self.assertRedirects(r, f'/order/{self.order.order_number}/', fetch_redirect_response=False)


class OrderListViewTest(TestCase):
    def setUp(self):
        user, cart, address, _ = setup_world('ol@t.id')
        self.client.force_login(user)
        self.order = checkout(cart, address, PaymentMethod.COD)

    def test_requires_login(self):
        self.client.logout()
        r = self.client.get('/order/')
        self.assertEqual(r.status_code, 302)

    def test_shows_orders(self):
        r = self.client.get('/order/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.order.order_number)


class CancelViewTest(TestCase):
    def setUp(self):
        user, cart, address, self.product = setup_world('ca@t.id')
        self.client.force_login(user)
        self.order = checkout(cart, address, PaymentMethod.COD)

    def test_cancel_pending_order(self):
        r = self.client.post(f'/order/{self.order.order_number}/cancel/', {'reason': 'Test'})
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, OrderStatus.CANCELLED)
        self.assertRedirects(r, f'/order/{self.order.order_number}/', fetch_redirect_response=False)
