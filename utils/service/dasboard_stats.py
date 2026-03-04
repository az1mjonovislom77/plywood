from decimal import Decimal
from django.utils import timezone
from product.models import Product
from order.models import OrderItem, Order
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Count, Value, DecimalField, ExpressionWrapper, Q


class DashboardStatsService:

    @classmethod
    def get_stats(cls):
        today = timezone.localdate()

        product_profit = ExpressionWrapper(
            (F("price") - F("product__arrival_price")) * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        debt_expr = ExpressionWrapper(
            F("total_price") - F("covered_amount"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        banding_expr = ExpressionWrapper(
            F("banding__length") * F("banding__thickness__price"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        product_stats = OrderItem.objects.aggregate(

            total_product_profit=Coalesce(
                Sum(product_profit),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            today_product_profit=Coalesce(
                Sum(product_profit, filter=Q(order__created_at__date=today)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )

        order_stats = Order.objects.aggregate(

            total_banding=Coalesce(
                Sum(banding_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            total_cutting=Coalesce(
                Sum("cutting__price"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            today_banding=Coalesce(
                Sum(banding_expr, filter=Q(created_at__date=today)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            today_cutting=Coalesce(
                Sum("cutting__price", filter=Q(created_at__date=today)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            total_sales=Count("id"),

            total_discount=Coalesce(
                Sum("discount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            total_debt=Coalesce(
                Sum(debt_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            today_debt=Coalesce(
                Sum(debt_expr, filter=Q(created_at__date=today)),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
        )

        total_income = (
                product_stats["total_product_profit"]
                + order_stats["total_banding"]
                + order_stats["total_cutting"]
        )

        today_income = (
                product_stats["today_product_profit"]
                + order_stats["today_banding"]
                + order_stats["today_cutting"]
        )

        return {
            "today_income": today_income,
            "total_income": total_income,
            "total_sales": order_stats["total_sales"],
            "total_discount": order_stats["total_discount"],
            "total_products": Product.objects.count(),
        }