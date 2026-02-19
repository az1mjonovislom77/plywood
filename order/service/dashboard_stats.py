from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from order.models import Order


class OrderStatsService:

    @staticmethod
    def get_stats():
        today = timezone.now().date()

        profit_expression = ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                              output_field=DecimalField(max_digits=14, decimal_places=2))
        stats = Order.objects.aggregate(
            total_sales=Coalesce(Count("id"), 0),
            today_income=Coalesce(Sum(profit_expression, filter=Q(order__created_at__date=today)), Decimal("0.00")),
            total_income=Coalesce(Sum(profit_expression), Decimal("0.00")),
        )

        return stats
