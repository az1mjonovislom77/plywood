from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal
from order.models import Order, Banding, Cutting


class DashboardStatsService:

    @staticmethod
    def get_cutting_banding_income():
        today = timezone.now().date()

        cutting_expr = ExpressionWrapper(
            F("price") * F("count"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        banding_expr = ExpressionWrapper(
            F("length") * F("thickness__price"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        cutting_stats = Cutting.objects.aggregate(
            total_cutting_income=Coalesce(Sum(cutting_expr), Decimal("0.00")),
            today_cutting_income=Coalesce(
                Sum(cutting_expr, filter=Q(created_at__date=today)),
                Decimal("0.00")
            ),
        )

        banding_stats = Banding.objects.aggregate(
            total_banding_income=Coalesce(Sum(banding_expr), Decimal("0.00")),
            today_banding_income=Coalesce(
                Sum(banding_expr, filter=Q(created_at__date=today)),
                Decimal("0.00")
            ),
        )

        stats = {
            **cutting_stats,
            **banding_stats
        }

        stats["total_income"] = (
            stats["total_cutting_income"] +
            stats["total_banding_income"]
        )

        stats["today_income"] = (
            stats["today_cutting_income"] +
            stats["today_banding_income"]
        )

        return stats