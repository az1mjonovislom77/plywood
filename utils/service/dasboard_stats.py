from decimal import Decimal
from django.db.models import F, Q, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from customer.models import BalanceHistory
from order.models import Banding, Cutting, Order, OrderItem
from supplier.models import SupplierTransaction
from utils.models import Expenses


class DashboardStatsService:
    @staticmethod
    def _day_range(target_date):
        start = timezone.make_aware(timezone.datetime.combine(target_date, timezone.datetime.min.time()))
        return start, start + timezone.timedelta(days=1)

    @classmethod
    def get_stats(cls, date_str=None):
        if date_str:
            target_date = parse_date(date_str)
            if not target_date:
                raise ValueError("Invalid date format")
        else:
            target_date = timezone.localdate()

        start, end = cls._day_range(target_date)

        product_sales_expr = ExpressionWrapper(
            F("price") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        banding_expr = ExpressionWrapper(
            F("length") * F("thickness__price"), output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        cutting_expr = ExpressionWrapper(
            F("price") * F("count"), output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        product_sales = OrderItem.objects.filter(order__created_at__gte=start, order__created_at__lt=end).aggregate(
            total=Coalesce(
                Sum(product_sales_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )["total"]

        banding_stats = Banding.objects.filter(created_at__gte=start, created_at__lt=end).aggregate(
            sales_total=Coalesce(
                Sum(banding_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            paid_total=Coalesce(
                Sum("covered_amount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        cutting_stats = Cutting.objects.filter(created_at__gte=start, created_at__lt=end).aggregate(
            sales_total=Coalesce(
                Sum(cutting_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            paid_total=Coalesce(
                Sum("covered_amount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        order_stats = Order.objects.filter(created_at__gte=start, created_at__lt=end).aggregate(
            cash_total=Coalesce(
                Sum("covered_amount", filter=Q(payment_method__in=[Order.PaymentMethod.CASH, Order.PaymentMethod.NASIYA])),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            card_total=Coalesce(
                Sum("covered_amount", filter=Q(payment_method=Order.PaymentMethod.CARD)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            paid_total=Coalesce(
                Sum("covered_amount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        balance_stats = BalanceHistory.objects.filter(created_at__gte=start, created_at__lt=end).aggregate(
            paid_total=Coalesce(
                Sum("amount", filter=Q(type=BalanceHistory.Type.PAYMENT)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            added_total=Coalesce(
                Sum("amount", filter=Q(type=BalanceHistory.Type.DEBT_ADD)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        today_expense = Expenses.objects.filter(
            created_at__gte=start,
            created_at__lt=end,
            expense_status=Expenses.ExpensesStatus.ACCEPT,
        ).aggregate(
            total=Coalesce(
                Sum("value"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )["total"]

        today_supplier_payments = SupplierTransaction.objects.filter(
            created_at__gte=start, created_at__lt=end
        ).aggregate(
            total=Coalesce(
                Sum("amount", filter=Q(transaction_type=SupplierTransaction.TransactionType.PAYMENT)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )["total"]

        today_cash = (
            order_stats["paid_total"]
            + banding_stats["paid_total"]
            + cutting_stats["paid_total"]
            + balance_stats["paid_total"]
            - today_expense
            - today_supplier_payments
        )

        return {
            "date": target_date,
            "today_cash": today_cash,
            "today_paid_debt": balance_stats["paid_total"],
            "today_added_debt": balance_stats["added_total"],
            "today_expense": today_expense,
            "today_supplier_payments": today_supplier_payments,
            "total_product_sales": product_sales,
            "total_banding_sales": banding_stats["sales_total"],
            "total_cutting_sales": cutting_stats["sales_total"],
            "total_cash_sales": order_stats["cash_total"],
            "total_card_sales": order_stats["card_total"],
        }
