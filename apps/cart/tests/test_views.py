from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.produk.models import Grade, Product, Series, Timeline
from apps.cart.models import Cart, CartItem


def make_user(email='buyer@harohub.id', password='Pass123!'):
    return User.objects.create_user(email=email, password=password, first_name='Buyer')


def make_product(name='HG Zaku', stock=10, status='ACTIVE', price=100000):
    tl, _ = Timeline.objects.get_or_create(slug='uc', defaults={'name': 'Universal Century'})
    sr, _ = Series.objects.get_or_create(slug='0079', defaults={'name': '0079', 'timeline': tl})
    gr, _ = Grade.objects.get_or_create(slug='hg', defaults={'name': 'High Grade', 'scale': '1/144'})
    return Product.objects.get_or_create(
        slug=name.lower().replace(' ', '-'),
        defaults={'name': name, 'grade': gr, 'series': sr, 'price': price, 'stock': stock, 'status': status},
    )[0]


class CartIndexTest(TestCase):
    def test_requires_login(self):
        r = self.client.get('/cart/')
        self.assertEqual(r.status_code, 302)

    def test_empty_cart_ok(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/cart/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'kosong')

    def test_shows_items(self):
        u = make_user()
        self.client.force_login(u)
        p = make_product()
        cart = Cart.objects.create(user=u)
        CartItem.objects.create(cart=cart, product=p, quantity=2)
        r = self.client.get('/cart/')
        self.assertContains(r, p.name)


class AddToCartTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.product = make_product()

    def test_get_redirects(self):
        r = self.client.get(f'/cart/add/{self.product.id}/')
        self.assertRedirects(r, '/', fetch_redirect_response=False)

    def test_post_creates_item(self):
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 2})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)

    def test_post_increments_existing(self):
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 1})
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 3})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, 4)

    def test_quantity_capped_at_stock(self):
        self.client.post(f'/cart/add/{self.product.id}/', {'quantity': 99})
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.first().quantity, self.product.stock)

    def test_out_of_stock_blocked(self):
        p = make_product('Empty Kit', stock=0)
        r = self.client.post(f'/cart/add/{p.id}/', {'quantity': 1})
        self.assertFalse(Cart.objects.filter(user=self.user).exists() and
                         Cart.objects.filter(user=self.user).first() and
                         Cart.objects.get(user=self.user).items.filter(product=p).exists()
                         if Cart.objects.filter(user=self.user).exists() else False)

    def test_discontinued_returns_404(self):
        p = make_product('Old Kit', status='DISCONTINUED')
        r = self.client.post(f'/cart/add/{p.id}/', {'quantity': 1})
        self.assertEqual(r.status_code, 404)


class UpdateItemTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.product = make_product()
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_update_quantity(self):
        self.client.post(f'/cart/update/{self.item.id}/', {'quantity': 5})
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 5)

    def test_quantity_zero_deletes_item(self):
        self.client.post(f'/cart/update/{self.item.id}/', {'quantity': 0})
        self.assertFalse(CartItem.objects.filter(pk=self.item.pk).exists())

    def test_other_users_item_404(self):
        other = make_user('other@harohub.id')
        other_cart = Cart.objects.create(user=other)
        other_item = CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)
        r = self.client.post(f'/cart/update/{other_item.id}/', {'quantity': 3})
        self.assertEqual(r.status_code, 404)

    def test_htmx_returns_partial(self):
        r = self.client.post(
            f'/cart/update/{self.item.id}/',
            {'quantity': 3},
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'cart-content')


class RemoveItemTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.product = make_product()
        self.cart = Cart.objects.create(user=self.user)
        self.item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_removes_item(self):
        self.client.post(f'/cart/remove/{self.item.id}/')
        self.assertFalse(CartItem.objects.filter(pk=self.item.pk).exists())

    def test_other_users_item_404(self):
        other = make_user('other2@harohub.id')
        other_cart = Cart.objects.create(user=other)
        other_item = CartItem.objects.create(cart=other_cart, product=self.product, quantity=1)
        r = self.client.post(f'/cart/remove/{other_item.id}/')
        self.assertEqual(r.status_code, 404)

    def test_htmx_returns_partial(self):
        r = self.client.post(
            f'/cart/remove/{self.item.id}/',
            HTTP_HX_REQUEST='true',
        )
        self.assertEqual(r.status_code, 200)
