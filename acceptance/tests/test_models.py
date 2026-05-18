import time
from datetime import date
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from product.models import Product
from supplier.models import Supplier
from user.models import User
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.core.exceptions import ValidationError
from acceptance.api.serializers import AcceptanceSerializer
from acceptance.api.views.acceptance_views import AcceptanceExportViewSet, AcceptanceViewSet
from acceptance.models import CurrencyRate, Acceptance
from acceptance.service.acceptance_export import AcceptanceExportService
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService


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

    def test_acceptance_serializer_count_trims_trailing_zeroes(self):
        acceptance = Acceptance.objects.create(product=self.product, count=Decimal("25.000"))

        data = AcceptanceSerializer(acceptance).data

        self.assertEqual(data["count"], "25")

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


class SupplierAcceptanceAPIViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="manager", password="123", role=User.UserRoles.MANAGER)
        self.product = Product.objects.create(name="Test Product")
        self.supplier = Supplier.objects.create(full_name="Test Supplier")
        self.other_supplier = Supplier.objects.create(full_name="Other Supplier")

    def test_supplier_acceptances_returns_date_filtered_acceptances_with_history(self):
        acceptance = AcceptanceWorkflowService.create(
            data={
                "product": self.product,
                "supplier": self.supplier,
                "arrival_price": Decimal("1000.00"),
                "sale_price": Decimal("1500.00"),
                "count": Decimal("25.000"),
            },
            user=self.user,
        )
        Acceptance.objects.create(product=self.product, supplier=self.other_supplier)

        request = self.factory.get(
            f"/acceptance/acceptances/supplier/{self.supplier.id}/",
            {"date": timezone.localdate().isoformat()},
        )
        force_authenticate(request, user=self.user)
        view = AcceptanceViewSet.as_view({"get": "supplier_acceptances"})

        response = view(request, supplier_id=self.supplier.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], acceptance.id)
        self.assertEqual(response.data[0]["count"], "25")
        self.assertEqual(len(response.data[0]["history"]), 1)

    def test_supplier_acceptances_rejects_invalid_date(self):
        request = self.factory.get(f"/acceptance/acceptances/supplier/{self.supplier.id}/", {"date": "bad-date"})
        force_authenticate(request, user=self.user)
        view = AcceptanceViewSet.as_view({"get": "supplier_acceptances"})

        response = view(request, supplier_id=self.supplier.id)

        self.assertEqual(response.status_code, 400)

    def test_analytics_excel_endpoint_returns_xlsx(self):
        Acceptance.objects.create(
            product=self.product,
            supplier=self.supplier,
            arrival_price=Decimal("1000.00"),
            count=Decimal("2.000"),
            acceptance_status=Acceptance.AcceptanceStatus.ACCEPT,
            arrival_date=date(2026, 4, 20),
        )
        request = self.factory.get(
            "/acceptance/acceptance-export/analytics/",
            {"from": "2026-04-20", "to": "2026-04-20"},
        )
        force_authenticate(request, user=self.user)
        view = AcceptanceExportViewSet.as_view({"get": "analytics_excel"})

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="acceptance_analytics.xlsx"')
        self.assertEqual(response.get("Content-Type"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_acceptance_keeps_product_arrival_price_in_original_dollar(self):
        CurrencyRate.objects.create(date=date(2026, 4, 20), rate=Decimal("12500.00"))
        acceptance = AcceptanceWorkflowService.create(
            data={
                "product": self.product,
                "supplier": self.supplier,
                "arrival_price": Decimal("20.00"),
                "sale_price": Decimal("25.00"),
                "price_type": Acceptance.PriceType.DOLLAR,
                "count": Decimal("1.000"),
                "arrival_date": date(2026, 4, 20),
            },
            user=self.user,
        )

        AcceptanceWorkflowService.accept(acceptance.id, self.user)
        self.product.refresh_from_db()

        self.assertEqual(self.product.arrival_price, Decimal("250000.00"))
        self.assertEqual(self.product.arrival_price_in_dollar, Decimal("20.00"))


class AcceptanceAnalyticsExportServiceTest(TestCase):
    def test_build_analytics_excel_groups_suppliers_by_date(self):
        report_date = date(2026, 4, 20)
        data = [
            {
                "date": report_date,
                "suppliers": [
                    {
                        "supplier_id": 1,
                        "supplier_name": "Mirmuhsin",
                        "total_quantity": Decimal("570"),
                        "total_investment": Decimal("157538850"),
                    }
                ],
            }
        ]

        wb = AcceptanceExportService.build_analytics_excel(data)
        ws = wb.active

        self.assertEqual(ws.title, "Analytics")
        self.assertEqual([ws["A3"].value, ws["B3"].value, ws["C3"].value, ws["D3"].value],
                         ["Sana", "Yetkazib beruvchi", "Miqdor", "Investitsiya"])
        self.assertEqual(ws["A4"].value, "20.04.2026")
        self.assertEqual(ws["B4"].value, "1 ta yetkazib beruvchi")
        self.assertEqual(ws["B5"].value, "Mirmuhsin")
        self.assertEqual(ws["C5"].value, 570.0)
        self.assertEqual(ws["D5"].value, 157538850.0)
