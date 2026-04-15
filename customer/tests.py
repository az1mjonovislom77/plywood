from decimal import Decimal
from django.test import TestCase
from customer.models import BalanceHistory, Customer
from customer.service.cover_debt import DebtService
from order.models import Order
from user.models import User


class DebtServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="seller", password="123", role=User.UserRoles.SELLER)
        self.customer = Customer.objects.create(full_name="Test Customer", debt=Decimal("100.00"))
        self.order = Order.objects.create(
            user=self.user,
            customer=self.customer,
            is_anonymous=False,
            payment_method=Order.PaymentMethod.NASIYA,
            total_price=Decimal("100.00"),
            covered_amount=Decimal("10.00"),
        )

    def test_cover_debt_does_not_mutate_existing_orders(self):
        DebtService.cover_debt(self.customer.id, Decimal("40.00"))

        self.order.refresh_from_db()
        self.customer.refresh_from_db()

        self.assertEqual(self.order.covered_amount, Decimal("10.00"))
        self.assertEqual(self.customer.debt, Decimal("60.00"))
        self.assertEqual(self.customer.covered_debt, Decimal("40.00"))
        self.assertTrue(
            BalanceHistory.objects.filter(
                customer=self.customer,
                type=BalanceHistory.Type.PAYMENT,
                amount=Decimal("40.00"),
            ).exists()
        )
