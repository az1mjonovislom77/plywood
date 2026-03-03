import time
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from product.models import Product
from supplier.models import Supplier
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError
from acceptance.models import CurrencyRate, Acceptance


class CurrencyRateModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_rate = CurrencyRate.objects.create(
            date=date(2024, 1, 1),
            rate=Decimal("10000.00"))

    def test_str_representation(self):
        self.assertEqual(str(self.existing_rate), "2024-01-01 - 10000.00")

    def test_date_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            CurrencyRate.objects.create(
                date=date(2024, 1, 1),
                rate=Decimal("9999.99"))


class AcceptanceModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(name="Test Product")
        cls.supplier = Supplier.objects.create(full_name="Test Supplier")

    def test_acceptance_creation(self):
        acceptance = Acceptance.objects.create(
            product=self.product,
            supplier=self.supplier,
            arrival_price=Decimal("1000.00"),
            sale_price=Decimal("1500.00"),
            count=5
        )

        self.assertEqual(acceptance.product, self.product)
        self.assertEqual(acceptance.supplier, self.supplier)
        self.assertEqual(acceptance.arrival_price, Decimal("1000.00"))
        self.assertEqual(acceptance.sale_price, Decimal("1500.00"))
        self.assertEqual(acceptance.price_type, Acceptance.PriceType.SUM)
        self.assertEqual(acceptance.count, 5)
        self.assertEqual(acceptance.arrival_date, timezone.localdate())
        self.assertIsNotNone(acceptance.created_at)

    def test_product_protect_on_delete(self):
        Acceptance.objects.create(product=self.product)

        with self.assertRaises(ProtectedError):
            self.product.delete()

    def test_supplier_set_null_on_delete(self):
        acceptance = Acceptance.objects.create(product=self.product, supplier=self.supplier)
        self.supplier.delete()
        acceptance.refresh_from_db()

        self.assertIsNone(acceptance.supplier)

    def test_str_representation(self):
        acceptance = Acceptance.objects.create(product=self.product)
        expected = f"{acceptance.id} - {self.product.name}"
        self.assertEqual(str(acceptance), expected)

    def test_invalid_price_type(self):
        acceptance = Acceptance(product=self.product, price_type="invalid")

        with self.assertRaises(ValidationError):
            acceptance.full_clean()

    def test_ordering_by_created_at_desc(self):
        first = Acceptance.objects.create(product=self.product)
        time.sleep(0.01)
        second = Acceptance.objects.create(product=self.product)

        acceptances = list(Acceptance.objects.all())

        self.assertEqual(acceptances[0], second)
        self.assertEqual(acceptances[1], first)
