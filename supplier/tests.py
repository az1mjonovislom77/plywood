from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from acceptance.models import Acceptance
from product.models import Product
from supplier.api.views.supplier_views import SupplierViewSet
from supplier.models import Supplier
from user.models import User


class SupplierViewSetTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="manager", password="123", role=User.UserRoles.MANAGER)
        self.product = Product.objects.create(name="Plywood")
        self.supplier = Supplier.objects.create(full_name="Supplier", phone_number="123")
        self.other_supplier = Supplier.objects.create(full_name="Other Supplier", phone_number="456")

    def test_list_returns_daily_acceptance_count_and_investment(self):
        Acceptance.objects.create(
            product=self.product,
            supplier=self.supplier,
            arrival_price=Decimal("1000.00"),
            count=Decimal("25.000"),
        )
        Acceptance.objects.create(
            product=self.product,
            supplier=self.supplier,
            arrival_price=Decimal("2000.00"),
            count=Decimal("2.500"),
        )
        Acceptance.objects.create(
            product=self.product,
            supplier=self.other_supplier,
            arrival_price=Decimal("9000.00"),
            count=Decimal("1.000"),
        )

        request = self.factory.get("/supplier/supplier/", {"date": timezone.localdate().isoformat()})
        force_authenticate(request, user=self.user)
        view = SupplierViewSet.as_view({"get": "list"})

        response = view(request)

        self.assertEqual(response.status_code, 200)
        supplier_data = next(item for item in response.data if item["id"] == self.supplier.id)
        self.assertEqual(supplier_data["daily_acceptance_count"], "27.5")
        self.assertEqual(supplier_data["daily_investment"], "30000.00")

    def test_list_uses_date_param(self):
        acceptance = Acceptance.objects.create(
            product=self.product,
            supplier=self.supplier,
            arrival_price=Decimal("1000.00"),
            count=Decimal("25.000"),
        )
        yesterday = timezone.now() - timedelta(days=1)
        Acceptance.objects.filter(id=acceptance.id).update(created_at=yesterday)

        request = self.factory.get("/supplier/supplier/", {"date": yesterday.date().isoformat()})
        force_authenticate(request, user=self.user)
        view = SupplierViewSet.as_view({"get": "list"})

        response = view(request)

        self.assertEqual(response.status_code, 200)
        supplier_data = next(item for item in response.data if item["id"] == self.supplier.id)
        self.assertEqual(supplier_data["daily_acceptance_count"], "25")
        self.assertEqual(supplier_data["daily_investment"], "25000.00")
