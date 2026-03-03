from decimal import Decimal
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_date
from django.utils import timezone
from order.models import OrderItem, Order


class DashboardStatsService:

    @staticmethod
    def _product_profit_expression():
        return ExpressionWrapper((F("price") - F("product__arrival_price")) * F("quantity"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @classmethod
    def get_range_stats(cls, date_from=None, date_to=None):
        today = timezone.localdate()

        if not date_from or not date_to:
            start_date = today
            end_date = today
        else:
            start_date = parse_date(date_from)
            end_date = parse_date(date_to)

            if not start_date or not end_date:
                raise ValueError("Invalid date format")

        date_filter_items = Q(order__created_at__date__range=(start_date, end_date))
        date_filter_orders = Q(created_at__date__range=(start_date, end_date))

        product_profit_expr = cls._product_profit_expression()

        product_income = OrderItem.objects.filter(date_filter_items).aggregate(
            total=Coalesce(
                Sum(product_profit_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        banding_income = Order.objects.filter(date_filter_orders).aggregate(
            total=Coalesce(
                Sum("banding__thickness__price"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_income = Order.objects.filter(date_filter_orders).aggregate(
            total=Coalesce(
                Sum("cutting__price"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        total_income = product_income + banding_income + cutting_income

        return {
            "from": start_date,
            "to": end_date,
            "total_income": total_income,
            "product_income": product_income,
            "banding_income": banding_income,
            "cutting_income": cutting_income,
        }
