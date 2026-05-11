from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_date
from customer.models import BalanceHistory
from order.models import Order, Banding, Cutting
from utils.models import Expenses
from utils.service.comprehensive_stats import DashboardStatsService


class FinanceReportJsonService:
    @classmethod
    def build(cls, date_from=None, date_to=None):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today

        start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(
            timezone.datetime.combine(end_date + timedelta(days=1), timezone.datetime.min.time()))

        income_orders = Order.objects.select_related("customer").filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            order_status=Order.OrderStatus.ACCEPT,
            covered_amount__gt=0,
        )

        expenses = Expenses.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            expense_status__in=[
                Expenses.ExpensesStatus.ACCEPT,
                Expenses.ExpensesStatus.CREATED,
            ]).order_by("created_at")

        income_map = defaultdict(Decimal)

        for order in income_orders:
            if order.customer:
                income_map[
                    (order.customer.id, order.customer.full_name)
                ] += Decimal(str(order.covered_amount))

        for banding in Banding.objects.filter(
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                covered_amount__gt=0,
        ).select_related("customer"):

            if banding.customer:
                income_map[
                    (banding.customer.id, banding.customer.full_name)
                ] += Decimal(str(banding.covered_amount))

        for cutting in Cutting.objects.filter(
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                covered_amount__gt=0,
        ).select_related("customer"):

            if cutting.customer:
                income_map[
                    (cutting.customer.id, cutting.customer.full_name)
                ] += Decimal(str(cutting.covered_amount))

        for payment in BalanceHistory.objects.filter(
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                type=BalanceHistory.Type.PAYMENT,
                amount__gt=0,
        ).select_related("customer"):

            if payment.customer:
                income_map[
                    (payment.customer.id, payment.customer.full_name)
                ] += Decimal(str(payment.amount))

        income = []
        income_total = Decimal("0")

        for (customer_id, customer_name), amount in income_map.items():
            income.append({
                "customer_id": customer_id,
                "customer": customer_name,
                "paid": amount,
            })

            income_total += amount

        expense_data = []
        expense_total = Decimal("0")

        for item in expenses:
            expense_data.append({
                "id": item.id,
                "description": item.description,
                "date": item.created_at.strftime("%d.%m.%Y"),
                "value": item.value,
            })

            expense_total += Decimal(str(item.value))

        return {
            "from": str(start_date),
            "to": str(end_date),
            "income": income,
            "income_total": income_total,
            "expenses": expense_data,
            "expense_total": expense_total,
            "opening_balance": Decimal(
                str(DashboardStatsService._cashbox_total(end_dt=start_dt - timedelta(microseconds=1)))),
            "closing_balance": Decimal(str(DashboardStatsService._cashbox_total(end_dt=end_dt))
                                       ),
        }
