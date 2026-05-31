from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Address, User


def make_user(email='test@harohub.id', password='TestPass123!', **kw):
    return User.objects.create_user(email=email, password=password, first_name='Test', **kw)


def make_address(user, *, is_default=False, city='Jakarta'):
    return Address.objects.create(
        user=user,
        recipient_name='Test User',
        phone='081234567890',
        full_address='Jl. Test No. 1',
        city=city,
        postal_code='12345',
        is_default=is_default,
    )


class RegisterViewTest(TestCase):
    def test_get(self):
        r = self.client.get('/accounts/register/')
        self.assertEqual(r.status_code, 200)

    def test_post_valid_creates_user_and_logs_in(self):
        r = self.client.post('/accounts/register/', {
            'email': 'baru@harohub.id',
            'first_name': 'Baru',
            'last_name': '',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertRedirects(r, '/accounts/profile/')
        self.assertTrue(User.objects.filter(email='baru@harohub.id').exists())

    def test_post_invalid_stays(self):
        r = self.client.post('/accounts/register/', {'email': 'bad'})
        self.assertEqual(r.status_code, 200)

    def test_authenticated_redirects(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/accounts/register/')
        self.assertRedirects(r, '/')


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_get(self):
        r = self.client.get('/accounts/login/')
        self.assertEqual(r.status_code, 200)

    def test_post_valid(self):
        r = self.client.post('/accounts/login/', {
            'email': 'test@harohub.id',
            'password': 'TestPass123!',
        })
        self.assertRedirects(r, '/')

    def test_post_wrong_password(self):
        r = self.client.post('/accounts/login/', {
            'email': 'test@harohub.id',
            'password': 'wrong',
        })
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'salah')

    def test_next_redirect(self):
        r = self.client.post('/accounts/login/?next=/accounts/profile/', {
            'email': 'test@harohub.id',
            'password': 'TestPass123!',
        })
        self.assertRedirects(r, '/accounts/profile/')


class LogoutViewTest(TestCase):
    def test_post_logs_out(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.post('/accounts/logout/')
        self.assertRedirects(r, '/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_get_redirects_without_logout(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/accounts/logout/')
        self.assertRedirects(r, '/')
        # GET tidak logout
        self.assertIn('_auth_user_id', self.client.session)


class ProfileViewTest(TestCase):
    def test_requires_login(self):
        r = self.client.get('/accounts/profile/')
        self.assertRedirects(r, '/accounts/login/?next=/accounts/profile/')

    def test_authenticated_ok(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/accounts/profile/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, u.email)

    def test_shows_wishlist_and_order_sections(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/accounts/profile/')
        self.assertContains(r, 'Wishlist Saya')
        self.assertContains(r, 'Pesanan Terakhir')


class WishlistPageTest(TestCase):
    def _make_product(self):
        from apps.catalog.models import Grade, Product, Series, Timeline
        tl, _ = Timeline.objects.get_or_create(slug='uc', defaults={'name': 'UC'})
        sr, _ = Series.objects.get_or_create(slug='sr', defaults={'name': 'SR', 'timeline': tl})
        gr, _ = Grade.objects.get_or_create(slug='hg', defaults={'name': 'HG', 'scale': '1/144'})
        return Product.objects.create(
            slug='hg-zaku', name='HG Zaku', grade=gr, series=sr, price=100000, stock=5,
        )

    def test_requires_login(self):
        r = self.client.get('/accounts/wishlist/')
        self.assertRedirects(r, '/accounts/login/?next=/accounts/wishlist/')

    def test_empty_state(self):
        u = make_user()
        self.client.force_login(u)
        r = self.client.get('/accounts/wishlist/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'kosong')

    def test_shows_wishlisted_product(self):
        from apps.recommendations.models import Wishlist
        u = make_user()
        self.client.force_login(u)
        product = self._make_product()
        Wishlist.objects.create(user=u, product=product)
        r = self.client.get('/accounts/wishlist/')
        self.assertContains(r, 'HG Zaku')


class ProfileEditViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_get(self):
        r = self.client.get('/accounts/profile/edit/')
        self.assertEqual(r.status_code, 200)

    def test_post_updates_user(self):
        r = self.client.post('/accounts/profile/edit/', {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '',
            'date_of_birth': '',
        })
        self.assertRedirects(r, '/accounts/profile/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')


class AddressViewTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)
        self.address = make_address(self.user, is_default=True)

    def test_create_address(self):
        r = self.client.post('/accounts/addresses/add/', {
            'recipient_name': 'New Recipient',
            'phone': '089876543210',
            'full_address': 'Jl. Baru No. 99',
            'city': 'Bandung',
            'postal_code': '40000',
            'notes': '',
            'is_default': '',
            'place_id': '',
            'latitude': '',
            'longitude': '',
        })
        self.assertRedirects(r, '/accounts/profile/')
        self.assertEqual(self.user.addresses.count(), 2)

    def test_update_address(self):
        r = self.client.post(f'/accounts/addresses/{self.address.pk}/edit/', {
            'recipient_name': 'Updated Name',
            'phone': '081234567890',
            'full_address': 'Jl. Test No. 1',
            'city': 'Jakarta',
            'postal_code': '12345',
            'notes': '',
            'is_default': 'on',
            'place_id': '',
            'latitude': '',
            'longitude': '',
        })
        self.assertRedirects(r, '/accounts/profile/')
        self.address.refresh_from_db()
        self.assertEqual(self.address.recipient_name, 'Updated Name')

    def test_delete_address(self):
        r = self.client.post(f'/accounts/addresses/{self.address.pk}/delete/')
        self.assertRedirects(r, '/accounts/profile/')
        self.assertEqual(self.user.addresses.count(), 0)

    def test_delete_other_users_address_returns_404(self):
        other = make_user('other@harohub.id')
        other_addr = make_address(other)
        r = self.client.post(f'/accounts/addresses/{other_addr.pk}/delete/')
        self.assertEqual(r.status_code, 404)

    def test_set_default_clears_others(self):
        addr2 = make_address(self.user, city='Surabaya')
        self.client.post(f'/accounts/addresses/{addr2.pk}/default/')
        self.address.refresh_from_db()
        addr2.refresh_from_db()
        self.assertFalse(self.address.is_default)
        self.assertTrue(addr2.is_default)
