from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from product.models import Product
from user.models import User
from utils.api.views.utils import LowStockNotificationView
from utils.models import NotificationSettings


class LowStockNotificationViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(username="manager", password="123", role=User.UserRoles.MANAGER)
        NotificationSettings.objects.create(low_stock_threshold=20)

    def test_low_stock_notifications_are_paginated(self):
        for index in range(25):
            Product.objects.create(name=f"Product {index}", count=Decimal("5.000"))

        view = LowStockNotificationView.as_view()
        request = self.factory.get("/utils/notifications/low-stock/?limit=10")
        force_authenticate(request, user=self.user)

        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["limit"], 10)
        self.assertEqual(response.data["total"], 25)
        self.assertEqual(response.data["total_pages"], 3)
        self.assertEqual(response.data["low_stock_products"], 25)
        self.assertEqual(len(response.data["products"]), 10)
