from decimal import Decimal
from django.db.models import (F, Sum, Count, Value, DecimalField, ExpressionWrapper, Q)
from django.db.models.functions import Coalesce
from django.utils import timezone
from order.models import OrderItem, Order
from product.models import Product


class DashboardStatsService:

    @staticmethod
    def _profit_expression():
        return ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2), )

    @classmethod
    def get_stats(cls):
        today = timezone.localdate()
        profit_expr = cls._profit_expression()

        orderitem_agg = OrderItem.objects.aggregate(
            total_income=Coalesce(
                Sum(profit_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            today_income=Coalesce(
                Sum(profit_expr,
                    filter=Q(order__created_at__date=today)), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        order_agg = Order.objects.aggregate(
            total_sales=Count("id"),
            total_discount=Coalesce(
                Sum("discount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        total_products = Product.objects.count()

        return {
            "today_income": orderitem_agg["today_income"],
            "total_income": orderitem_agg["total_income"],
            "total_sales": order_agg["total_sales"],
            "total_discount": order_agg["total_discount"],
            "total_products": total_products,
        }
