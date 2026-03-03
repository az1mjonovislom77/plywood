from decimal import Decimal
from django.utils import timezone
from order.models import OrderItem, Order
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q


class DailyDashboardStatsService:

    @staticmethod
    def _product_gross_expression():
        return ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField(max_digits=14, decimal_places=2))

    @classmethod
    def get_daily_stats(cls, date_str=None):

        if date_str:
            target_date = parse_date(date_str)
            if not target_date:
                raise ValueError("Invalid date format")
        else:
            target_date = timezone.localdate()

        item_filter = Q(order__created_at__date=target_date)
        order_filter = Q(created_at__date=target_date)

        product_gross_expr = cls._product_gross_expression()
        product_sales = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_gross_expr),
                Value(Decimal("0.00")), output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        banding_income = Order.objects.filter(order_filter).aggregate(
            total=Coalesce(
                Sum("banding__thickness__price"),
                Value(Decimal("0.00")), output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_income = Order.objects.filter(order_filter).aggregate(
            total=Coalesce(
                Sum("cutting__price"),
                Value(Decimal("0.00")), output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cashbox_total = product_sales + banding_income + cutting_income

        return {
            "date": target_date,
            "cashbox_total": cashbox_total,
            "product_sales": product_sales,
            "banding_income": banding_income,
            "cutting_income": cutting_income,
        }
