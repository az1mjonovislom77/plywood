from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from customer.models import Customer
from order.models import Order
from utils.models import Expenses
from utils.service.comprehensive_stats import DashboardStatsService


class FinanceReportJsonService:
    @classmethod
    def build(cls, date_from=None, date_to=None):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today
        start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))

        income_orders = Order.objects.select_related("customer").filter(
            created_at__range=(start_dt, end_dt)).exclude(order_status=Order.OrderStatus.CANCEL)

        expenses = Expenses.objects.filter(
            expense_status="accept",
            created_at__range=(start_dt, end_dt)).order_by("created_at")

        income = []
        income_total = 0

        for customer in Customer.objects.filter(orders__in=income_orders).distinct():
            paid = income_orders.filter(customer=customer).aggregate(total=Sum("covered_amount"))["total"] or 0
            income.append({
                "customer_id": customer.id,
                "customer": customer.full_name,
                "paid": paid,
            })
            income_total += paid

        expense_data = []
        expense_total = 0

        for item in expenses:
            expense_data.append({
                "id": item.id,
                "description": item.description,
                "date": item.created_at.strftime("%d.%m.%Y"),
                "value": item.value,
            })
            expense_total += item.value

        return {
            "from": str(start_date),
            "to": str(end_date),
            "income": income,
            "income_total": income_total,
            "expenses": expense_data,
            "expense_total": expense_total,
            "opening_balance": Decimal(str(DashboardStatsService._cashbox_total(end_dt=start_dt))),
            "closing_balance": Decimal(str(DashboardStatsService._cashbox_total(end_dt=end_dt)))
        }
