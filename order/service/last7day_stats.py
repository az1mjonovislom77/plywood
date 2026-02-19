from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from order.models import OrderItem


class Last7dayStatsService:
    @staticmethod
    def get_last_7_days_income():
        today = timezone.now().date()
        start_date = today - timedelta(days=6)

        profit_expr = ExpressionWrapper((F("sale_price") - F("product__arrival_price")) * F("quantity"),
                                        output_field=DecimalField(max_digits=14, decimal_places=2))

        queryset = (
            OrderItem.objects
            .filter(order__created_at__date__gte=start_date)
            .annotate(day=TruncDate("order__created_at"))
            .values("day")
            .annotate(income=Coalesce(Sum(profit_expr), Decimal("0.00")))
            .order_by("day")
        )

        result = []
        income_map = {item["day"]: item["income"] for item in queryset}

        for i in range(7):
            date = start_date + timedelta(days=i)
            result.append({
                "date": date,
                "income": income_map.get(date, Decimal("0.00"))
            })

        return result
