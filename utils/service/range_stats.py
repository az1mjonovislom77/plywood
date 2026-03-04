from decimal import Decimal
from django.utils import timezone
from order.models import OrderItem, Order
from django.utils.dateparse import parse_date
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q


class DashboardRangeStatsService:
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

        item_filter = Q(order__created_at__date__range=(start_date, end_date))
        order_filter = Q(created_at__date__range=(start_date, end_date))

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

        cutting_expr = ExpressionWrapper(
            F("cutting__price") * F("cutting__count"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )

        product_income = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_profit),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )["total"]

        order_stats = Order.objects.filter(order_filter).aggregate(

            banding_income=Coalesce(
                Sum(banding_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            cutting_income=Coalesce(
                Sum(cutting_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            total_discount=Coalesce(
                Sum("discount"),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),

            total_debt=Coalesce(
                Sum(debt_expr),
                Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )

        total_income = (product_income + order_stats["banding_income"] + order_stats["cutting_income"])

        return {
            "from": start_date,
            "to": end_date,
            "total_income": total_income,
            "product_income": product_income,
            "banding_income": order_stats["banding_income"],
            "cutting_income": order_stats["cutting_income"]
        }
