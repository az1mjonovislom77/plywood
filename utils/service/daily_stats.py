from decimal import Decimal
from django.utils import timezone
from order.models import OrderItem, Order, Banding, Cutting
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q


class DailyDashboardStatsService:

    @staticmethod
    def _product_gross_expression():
        return ExpressionWrapper(F("price") * F("quantity"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    def _debt_expression():
        return ExpressionWrapper(
            F("total_price") - Coalesce(F("covered_amount"), Value(0)),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

    @staticmethod
    def _banding_expression():
        return ExpressionWrapper(F("length") * F("thickness__price"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @staticmethod
    def _cutting_expression():
        return ExpressionWrapper(F("price") * F("count"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @classmethod
    def get_daily_stats(cls, date_str=None):

        if date_str:
            target_date = parse_date(date_str)
            if not target_date:
                raise ValueError("Invalid date format")
        else:
            target_date = timezone.localdate()

        item_filter = Q(
            order__accepted_at__date=target_date,
            order__order_status=Order.OrderStatus.ACCEPT
        )

        order_filter = Q(
            accepted_at__date=target_date,
            order_status=Order.OrderStatus.ACCEPT
        )

        product_gross_expr = cls._product_gross_expression()
        debt_expr = cls._debt_expression()
        banding_expr = cls._banding_expression()
        cutting_expr = cls._cutting_expression()

        product_sales = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_gross_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        order_stats = Order.objects.filter(order_filter).aggregate(
            total_debt=Coalesce(
                Sum(debt_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            total_discount=Coalesce(
                Sum("discount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))

        total_debt = order_stats["total_debt"]
        total_discount = order_stats["total_discount"]

        banding_income = Banding.objects.filter(created_at__date=target_date).aggregate(
            total=Coalesce(
                Sum(banding_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_income = Cutting.objects.filter(created_at__date=target_date).aggregate(
            total=Coalesce(
                Sum(cutting_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cashbox_total = (
                product_sales
                + banding_income
                + cutting_income
                - total_discount
                - total_debt
        )

        return {
            "date": target_date,
            "cashbox_total": cashbox_total,
            "product_sales": product_sales,
            "banding_income": banding_income,
            "cutting_income": cutting_income,
            "daily_debt": total_debt,
        }
