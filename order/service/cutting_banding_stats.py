from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from order.models import Order


class DashboardStatsService:

    @staticmethod
    def get_cutting_banding_income():
        today = timezone.now().date()
        cutting_expr = ExpressionWrapper(F("cutting__price") * F("cutting__count"),
                                         output_field=DecimalField(max_digits=14, decimal_places=2))

        banding_expr = ExpressionWrapper((F("banding__width") + F("banding__height")) *
                                         Decimal("2.0") * F("banding__thickness__price"),
                                         output_field=DecimalField(max_digits=14, decimal_places=2))

        stats = Order.objects.aggregate(
            total_cutting_income=Coalesce(Sum(cutting_expr), Decimal("0.00")),
            today_cutting_income=Coalesce(Sum(cutting_expr, filter=Q(created_at__date=today)), Decimal("0.00")),
            total_banding_income=Coalesce(Sum(banding_expr), Decimal("0.00")),
            today_banding_income=Coalesce(Sum(banding_expr, filter=Q(created_at__date=today)), Decimal("0.00")),
        )

        stats["total_income"] = (stats["total_cutting_income"] + stats["total_banding_income"])
        stats["today_income"] = (stats["today_cutting_income"] + stats["today_banding_income"])

        return stats
