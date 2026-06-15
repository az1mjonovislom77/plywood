from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from customer.api.views.customer import CustomerViewSet
from customer.models import BalanceHistory, Customer
from customer.service.customer_balance import CustomerBalanceService
from customer.service.cover_debt import DebtService
from order.models import Order
from user.models import User


class DebtServiceTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
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
                customer=self.customer, type=BalanceHistory.Type.PAYMENT,
                amount=Decimal("40.00")).exists()
        )

    def test_customer_list_is_paginated(self):
        for index in range(25):
            Customer.objects.create(full_name=f"Customer {index}")

        view = CustomerViewSet.as_view({"get": "list"})
        request = self.factory.get("/customer/customer/?limit=10")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["limit"], 10)
        self.assertEqual(response.data["total"], 26)
        self.assertEqual(response.data["total_pages"], 3)
        self.assertEqual(len(response.data["data"]), 10)

    def test_cover_debt_stores_amount_over_debt_as_overpayment(self):
        DebtService.cover_debt(self.customer.id, Decimal("150.00"))

        self.customer.refresh_from_db()

        self.assertEqual(self.customer.debt, Decimal("0.00"))
        self.assertEqual(self.customer.covered_debt, Decimal("100.00"))
        self.assertEqual(self.customer.overpayment, Decimal("50.00"))
        self.assertTrue(
            BalanceHistory.objects.filter(
                customer=self.customer,
                type=BalanceHistory.Type.PAYMENT,
                amount=Decimal("150.00")).exists()
        )

    def test_cover_debt_serializer_rejects_negative_amount(self):
        from customer.api.serializers import CoverDebtSerializer
        serializer = CoverDebtSerializer(data={"amount": "-10"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_cover_debt_serializer_rejects_zero_amount(self):
        from customer.api.serializers import CoverDebtSerializer
        serializer = CoverDebtSerializer(data={"amount": "0"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)

    def test_cover_debt_serializer_accepts_positive_amount(self):
        from customer.api.serializers import CoverDebtSerializer
        serializer = CoverDebtSerializer(data={"amount": "50.00"})
        self.assertTrue(serializer.is_valid())

    def test_bulk_customer_debt_matches_single_customer_debt(self):
        today = self.order.created_at.date()

        single_debt = CustomerBalanceService.calculate_customer_debt(
            customer=self.customer, date_from=today, date_to=today)
        bulk_debt = CustomerBalanceService.bulk_calculate_customer_debt(
            customers=[self.customer], date_from=today, date_to=today)[self.customer.id]

        self.assertEqual(bulk_debt, single_debt)
