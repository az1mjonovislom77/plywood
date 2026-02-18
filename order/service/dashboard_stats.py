from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from order.models import Order


class OrderStatsService:

    @staticmethod
    def get_stats():
        today = timezone.now().date()

        stats = Order.objects.aggregate(
            total_sales=Coalesce(Count("id"), 0),
            today_income=Coalesce(Sum("total_price", filter=Q(created_at__date=today)), Decimal("0.00")),
            total_income=Coalesce(Sum("total_price"), Decimal("0.00")),
        )

        return stats
