from decimal import Decimal
from django.db.models import F, Q, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from order.models import Banding, Cutting, OrderItem


class DashboardRangeStatsService:
    @staticmethod
    def _range_bounds(start_date, end_date):
        start = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end = timezone.make_aware(
            timezone.datetime.combine(end_date + timezone.timedelta(days=1), timezone.datetime.min.time())
        )
        return start, end

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

        start_dt, end_dt = cls._range_bounds(start_date, end_date)

        item_filter = Q(order__created_at__gte=start_dt, order__created_at__lt=end_dt)

        product_profit = ExpressionWrapper(
            (F("price") - F("product__arrival_price")) * F("quantity"),
            output_field=DecimalField(max_digits=14, decimal_places=2)
        )
        banding_expr = ExpressionWrapper(F("length") * F("thickness__price"),
                                         output_field=DecimalField(max_digits=14, decimal_places=2))
        cutting_expr = ExpressionWrapper(F("price") * F("count"),
                                         output_field=DecimalField(max_digits=14, decimal_places=2))

        product_income = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_profit), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        banding_income = Banding.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt).aggregate(
            total=Coalesce(
                Sum(banding_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_income = Cutting.objects.filter(created_at__gte=start_dt, created_at__lt=end_dt).aggregate(
            total=Coalesce(
                Sum(cutting_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        total_income = product_income + banding_income + cutting_income

        return {
            "from": start_date,
            "to": end_date,
            "total_income": total_income,
            "product_income": product_income,
            "banding_income": banding_income,
            "cutting_income": cutting_income
        }
