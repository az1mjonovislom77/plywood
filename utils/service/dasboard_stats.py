from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from order.models import Order
from product.models import Product


class DashboardStatsService:

    @staticmethod
    def get_stats():
        today = timezone.now().date()

        stats = Order.objects.aggregate(
            today_income=Coalesce(Sum("total_price", filter=Q(created_at__date=today)), Decimal("0.00")),
            total_income=Coalesce(Sum("total_price"), Decimal("0.00")),
            total_sales=Coalesce(Count("id"), 0),
            total_discount=Coalesce(Sum("discount"), Decimal("0.00")),
        )
        total_products = Product.objects.count()

        return {
            "today_income": stats["today_income"],
            "total_income": stats["total_income"],
            "total_sales": stats["total_sales"],
            "total_discount": stats["total_discount"],
            "total_products": total_products
        }
