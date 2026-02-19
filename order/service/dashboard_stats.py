from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from order.models import Order, OrderItem


class OrderStatsService:

    @staticmethod
    def get_stats():
        today = timezone.now().date()

        profit_expr = ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                        output_field=DecimalField(max_digits=14, decimal_places=2))
        stats = Order.objects.aggregate(
            total_sales=Coalesce(Count("id"), 0),
            today_income=OrderItem.objects.filter(order__created_at__date=today).aggregate(
                income=Coalesce(Sum(profit_expr), Decimal("0.00")))["income"],
            total_income=OrderItem.objects.aggregate(income=Coalesce(Sum(profit_expr), Decimal("0.00")))["income"],

        )

        return stats
