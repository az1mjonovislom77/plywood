from decimal import Decimal
from django.db.models import (
    F, Sum, Count, Value, DecimalField,
    ExpressionWrapper, Q
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from order.models import OrderItem, Order
from product.models import Product


class DashboardStatsService:

    @staticmethod
    def _product_profit_expression():
        return ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @classmethod
    def get_stats(cls):
        today = timezone.localdate()

        product_profit_expr = cls._product_profit_expression()

        product_agg = OrderItem.objects.aggregate(
            total_product_profit=Coalesce(
                Sum(product_profit_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            today_product_profit=Coalesce(
                Sum(
                    product_profit_expr,
                    filter=Q(order__created_at__date=today)
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )

        order_agg = Order.objects.aggregate(
            total_banding=Coalesce(
                Sum("banding__thickness__price"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            total_cutting=Coalesce(
                Sum("cutting__price"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            today_banding=Coalesce(
                Sum(
                    "banding__thickness__price",
                    filter=Q(created_at__date=today)
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            today_cutting=Coalesce(
                Sum(
                    "cutting__price",
                    filter=Q(created_at__date=today)
                ),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            total_sales=Count("id"),
            total_discount=Coalesce(
                Sum("discount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        total_income = (
                product_agg["total_product_profit"]
                + order_agg["total_banding"]
                + order_agg["total_cutting"]
        )

        today_income = (
                product_agg["today_product_profit"]
                + order_agg["today_banding"]
                + order_agg["today_cutting"]
        )

        total_products = Product.objects.count()

        return {
            "today_income": today_income,
            "total_income": total_income,
            "total_sales": order_agg["total_sales"],
            "total_discount": order_agg["total_discount"],
            "total_products": total_products,
            
        }
