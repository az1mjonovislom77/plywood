from decimal import Decimal
from django.utils import timezone
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from order.models import OrderItem, Order, Banding, Cutting
from customer.models import BalanceHistory
from utils.models import Expenses


class DashboardStatsService:

    @classmethod
    def get_stats(cls):
        today = timezone.localdate()
        product_sales_expr = ExpressionWrapper(
            F("price") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2))

        banding_expr = ExpressionWrapper(
            F("length") * F("thickness__price"), output_field=DecimalField(max_digits=14, decimal_places=2))

        cutting_expr = ExpressionWrapper(
            F("price") * F("count"), output_field=DecimalField(max_digits=14, decimal_places=2))

        product_sales = OrderItem.objects.aggregate(
            total=Coalesce(
                Sum(product_sales_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        banding_sales = Banding.objects.aggregate(
            total=Coalesce(Sum(banding_expr), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_sales = Cutting.objects.aggregate(
            total=Coalesce(Sum(cutting_expr), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        total_cash_sales = Order.objects.aggregate(
            total=Coalesce(
                Sum("total_price",
                    filter=Q(payment_method__in=[Order.PaymentMethod.CASH, Order.PaymentMethod.NASIYA])),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        total_card_sales = Order.objects.aggregate(
            total=Coalesce(Sum("total_price", filter=Q(payment_method=Order.PaymentMethod.CARD)),
                           Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        today_cash = Order.objects.aggregate(
            total=Coalesce(Sum("covered_amount", filter=Q(created_at__date=today)), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        today_paid_debt = BalanceHistory.objects.aggregate(
            total=Coalesce(Sum("amount", filter=Q(
                type=BalanceHistory.Type.PAYMENT, created_at__date=today)), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        today_added_debt = BalanceHistory.objects.aggregate(
            total=Coalesce(Sum("amount", filter=Q(
                type=BalanceHistory.Type.DEBT_ADD, created_at__date=today)), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        today_expense = Expenses.objects.aggregate(
            total=Coalesce(Sum("value", filter=Q(
                created_at__date=today, expense_status=Expenses.ExpensesStatus.ACCEPT)), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        return {
            "today_cash": today_cash,
            "today_paid_debt": today_paid_debt,
            "today_added_debt": today_added_debt,
            "today_expense": today_expense,
            "total_product_sales": product_sales,
            "total_banding_sales": banding_sales,
            "total_cutting_sales": cutting_sales,
            "total_cash_sales": total_cash_sales,
            "total_card_sales": total_card_sales,
        }
