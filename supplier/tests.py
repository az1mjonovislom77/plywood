from decimal import Decimal
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from supplier.models import Supplier, SupplierTransaction
from supplier.service.supplier import SupplierService


class SupplierPaymentServiceTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.create(full_name="Test Supplier")
        SupplierTransaction.objects.create(
            supplier=self.supplier,
            transaction_type=SupplierTransaction.TransactionType.PURCHASE,
            amount=Decimal("500.00"),
        )
        SupplierService.recalculate_debt(self.supplier)

    @patch("supplier.service.supplier.DashboardStatsService.get_stats")
    def test_make_payment_reduces_supplier_debt(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 1000.0}
        SupplierService.make_payment(self.supplier.id, Decimal("200.00"))
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.debt, Decimal("300.00"))

    @patch("supplier.service.supplier.DashboardStatsService.get_stats")
    def test_make_payment_rejects_zero_amount(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 1000.0}
        with self.assertRaises(ValidationError):
            SupplierService.make_payment(self.supplier.id, Decimal("0"))

    @patch("supplier.service.supplier.DashboardStatsService.get_stats")
    def test_make_payment_rejects_amount_exceeding_debt(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 1000.0}
        with self.assertRaises(ValidationError):
            SupplierService.make_payment(self.supplier.id, Decimal("600.00"))

    @patch("supplier.service.supplier.DashboardStatsService.get_stats")
    def test_make_payment_rejects_when_cashbox_insufficient(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 50.0}
        with self.assertRaises(ValidationError):
            SupplierService.make_payment(self.supplier.id, Decimal("200.00"))
