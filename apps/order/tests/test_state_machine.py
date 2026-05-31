from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.accounts.models import User
from apps.order.models import Order, OrderStatus


def make_order(status=OrderStatus.PENDING):
    user = User.objects.create_user(email=f'u{Order.objects.count()}@t.id', password='x')
    o = Order.objects.create(
        user=user, status=status,
        shipping_recipient_name='Test', shipping_phone='08x',
        shipping_full_address='Jl.', shipping_city='Jakarta', shipping_postal_code='10000',
        subtotal=100000, shipping_cost=15000, total=115000,
    )
    return o


class TransitionTest(TestCase):
    def test_pending_to_paid(self):
        o = make_order(OrderStatus.PENDING)
        o.transition_to(OrderStatus.PAID)
        self.assertEqual(o.status, OrderStatus.PAID)

    def test_paid_to_processing(self):
        o = make_order(OrderStatus.PAID)
        o.transition_to(OrderStatus.PROCESSING)
        self.assertEqual(o.status, OrderStatus.PROCESSING)

    def test_processing_to_shipped_sets_timestamp(self):
        o = make_order(OrderStatus.PROCESSING)
        self.assertIsNone(o.shipped_at)
        o.transition_to(OrderStatus.SHIPPED)
        o.refresh_from_db()
        self.assertIsNotNone(o.shipped_at)

    def test_shipped_to_completed_sets_timestamp(self):
        o = make_order(OrderStatus.SHIPPED)
        o.transition_to(OrderStatus.COMPLETED)
        o.refresh_from_db()
        self.assertIsNotNone(o.completed_at)

    def test_cancelled_sets_timestamp_and_reason(self):
        o = make_order(OrderStatus.PENDING)
        o.transition_to(OrderStatus.CANCELLED, reason='Test reason')
        o.refresh_from_db()
        self.assertIsNotNone(o.cancelled_at)
        self.assertEqual(o.cancellation_reason, 'Test reason')

    def test_invalid_transition_raises(self):
        o = make_order(OrderStatus.PENDING)
        with self.assertRaises(ValidationError):
            o.transition_to(OrderStatus.SHIPPED)

    def test_completed_is_terminal(self):
        o = make_order(OrderStatus.COMPLETED)
        with self.assertRaises(ValidationError):
            o.transition_to(OrderStatus.CANCELLED)

    def test_cancelled_is_terminal(self):
        o = make_order(OrderStatus.CANCELLED)
        with self.assertRaises(ValidationError):
            o.transition_to(OrderStatus.PAID)

    def test_order_number_generated(self):
        o = make_order()
        o.refresh_from_db()
        self.assertTrue(o.order_number.startswith('HH-'))
        self.assertIn(str(o.id).zfill(4), o.order_number)

    def test_is_cancellable(self):
        self.assertTrue(make_order(OrderStatus.PENDING).is_cancellable)
        self.assertTrue(make_order(OrderStatus.PAID).is_cancellable)
        self.assertTrue(make_order(OrderStatus.PROCESSING).is_cancellable)
        self.assertFalse(make_order(OrderStatus.SHIPPED).is_cancellable)
        self.assertFalse(make_order(OrderStatus.COMPLETED).is_cancellable)
