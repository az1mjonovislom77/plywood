from decimal import Decimal
from unittest.mock import patch
from user.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from product.models import Product
from utils.api.views.utils import LowStockNotificationView
from utils.models import NotificationSettings, Expenses
from utils.service.expenses_service import ExpensesWorkflowService


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


class ExpensesWorkflowServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="manager", password="123", role=User.UserRoles.MANAGER)

    @patch("utils.service.expenses_service.DashboardStatsService.get_stats")
    def test_create_small_expense_status_is_created(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 5_000_000}
        expense = ExpensesWorkflowService.create({"value": 500_000, "description": "Test"}, self.user)
        self.assertEqual(expense.expense_status, Expenses.ExpensesStatus.CREATED)

    def test_create_large_expense_status_is_waiting(self):
        expense = ExpensesWorkflowService.create({"value": 1_000_000, "description": "Big"}, self.user)
        self.assertEqual(expense.expense_status, Expenses.ExpensesStatus.WAITING)

    @patch("utils.service.expenses_service.DashboardStatsService.get_stats")
    def test_create_small_expense_insufficient_cashbox_raises_error(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 100}
        with self.assertRaises(ValueError):
            ExpensesWorkflowService.create({"value": 500_000, "description": "Test"}, self.user)

    @patch("utils.service.expenses_service.DashboardStatsService.get_stats")
    def test_accept_waiting_expense_changes_status(self, mock_stats):
        mock_stats.return_value = {"cashbox_total": 5_000_000}
        expense = Expenses.objects.create(
            user=self.user, value=500_000, description="Waiting",
            expense_status=Expenses.ExpensesStatus.WAITING
        )
        result = ExpensesWorkflowService.accept(expense.id, self.user)
        self.assertEqual(result.expense_status, Expenses.ExpensesStatus.ACCEPT)

    def test_accept_non_waiting_expense_raises_error(self):
        expense = Expenses.objects.create(
            user=self.user, value=500_000, description="Created",
            expense_status=Expenses.ExpensesStatus.CREATED
        )
        with self.assertRaises(ValueError):
            ExpensesWorkflowService.accept(expense.id, self.user)

    def test_cancel_waiting_expense_changes_status(self):
        expense = Expenses.objects.create(
            user=self.user, value=1_500_000, description="Pending",
            expense_status=Expenses.ExpensesStatus.WAITING
        )
        result = ExpensesWorkflowService.cancel(expense.id, self.user)
        self.assertEqual(result.expense_status, Expenses.ExpensesStatus.CANCEL)

    def test_cancel_non_waiting_expense_raises_error(self):
        expense = Expenses.objects.create(
            user=self.user, value=500_000, description="Already done",
            expense_status=Expenses.ExpensesStatus.ACCEPT
        )
        with self.assertRaises(ValueError):
            ExpensesWorkflowService.cancel(expense.id, self.user)
