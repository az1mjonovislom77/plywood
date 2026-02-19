from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Value, Count
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

from order.models import Order, OrderItem
from product.models import Product


class DashboardStatsService:

    @staticmethod
    def get_stats():
        today = timezone.now().date()

        profit_expr = ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                        output_field=DecimalField(max_digits=14, decimal_places=2))

        stats = Order.objects.aggregate(
            today_income=OrderItem.objects.filter(order__created_at__date=today).aggregate(
                income=Coalesce(Sum(profit_expr), Value(0),
                                output_field=DecimalField(max_digits=14, decimal_places=2)))["income"],
            total_income=OrderItem.objects.aggregate(income=Coalesce(Sum(profit_expr), Decimal("0.00")))["income"],
            total_sales=Coalesce(Count("id"), 0),
            total_discount=Coalesce(Sum("discount"), Decimal("0.00")))
        total_products = Product.objects.count()

        return {
            "today_income": stats["today_income"],
            "total_income": stats["total_income"],
            "total_sales": stats["total_sales"],
            "total_discount": stats["total_discount"],
            "total_products": total_products
        }
