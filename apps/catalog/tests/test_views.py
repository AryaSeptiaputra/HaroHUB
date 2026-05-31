from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Grade, Product, ProductStatus, Series, Timeline


def make_product(name='Test Kit', status='ACTIVE', stock=5):
    tl, _ = Timeline.objects.get_or_create(slug='uc', defaults={'name': 'Universal Century'})
    sr, _ = Series.objects.get_or_create(slug='0079', defaults={'name': 'Gundam 0079', 'timeline': tl})
    gr, _ = Grade.objects.get_or_create(slug='hg', defaults={'name': 'High Grade', 'scale': '1/144'})
    return Product.objects.get_or_create(
        slug=name.lower().replace(' ', '-'),
        defaults={'name': name, 'grade': gr, 'series': sr, 'price': 100000, 'stock': stock, 'status': status},
    )[0]


class ListingViewTest(TestCase):
    def setUp(self):
        self.p1 = make_product('HG Zaku II')
        self.p2 = make_product('MG Gelgoog', stock=0)
        self.discontinued = make_product('Old Kit', status='DISCONTINUED')

    def test_listing_ok(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'HG Zaku II')

    def test_discontinued_excluded(self):
        r = self.client.get('/')
        self.assertNotContains(r, 'Old Kit')

    def test_filter_by_grade(self):
        r = self.client.get('/?grade=hg')
        self.assertEqual(r.status_code, 200)

    def test_search(self):
        r = self.client.get('/?q=Zaku')
        self.assertContains(r, 'HG Zaku II')

    def test_pagination_param_preserved(self):
        r = self.client.get('/?grade=hg&page=1')
        self.assertEqual(r.status_code, 200)


class DetailViewTest(TestCase):
    def setUp(self):
        self.product = make_product('RG Char Zaku')

    def test_detail_ok(self):
        r = self.client.get(f'/catalog/{self.product.slug}/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'RG Char Zaku')

    def test_discontinued_returns_404(self):
        p = make_product('Disc Kit', status='DISCONTINUED')
        r = self.client.get(f'/catalog/{p.slug}/')
        self.assertEqual(r.status_code, 404)


class SearchAutocompleteTest(TestCase):
    def setUp(self):
        make_product('HG Unicorn Gundam')

    def test_empty_query_returns_empty(self):
        r = self.client.get('/catalog/search/?q=a')
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Unicorn')

    def test_two_char_query_returns_results(self):
        r = self.client.get('/catalog/search/?q=Un')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Unicorn')

    def test_no_match(self):
        r = self.client.get('/catalog/search/?q=XXXNOTEXIST')
        self.assertEqual(r.status_code, 200)
