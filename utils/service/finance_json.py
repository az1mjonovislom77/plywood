from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_date
from customer.models import BalanceHistory
from order.models import Order, Banding, Cutting
from utils.models import Expenses
from utils.service.comprehensive_stats import DashboardStatsService
from supplier.models import SupplierTransaction


class FinanceReportJsonService:
    @classmethod
    def build(cls, date_from=None, date_to=None):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today

        start_dt = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )

        end_dt = timezone.make_aware(
            timezone.datetime.combine(
                end_date + timedelta(days=1),
                timezone.datetime.min.time()
            )
        )

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
            ]
        ).order_by("created_at")

        supplier_payments = SupplierTransaction.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            transaction_type=SupplierTransaction.TransactionType.PAYMENT,
        ).select_related("supplier")

        income_map = defaultdict(Decimal)

        for order in income_orders:
            c_id = order.customer.id if order.customer else None
            c_name = order.customer.full_name if order.customer else "Anonim"
            income_map[(c_id, c_name)] += Decimal(str(order.covered_amount))

        for banding in Banding.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            covered_amount__gt=0,
        ).select_related("customer"):
            c_id = banding.customer.id if banding.customer else None
            c_name = banding.customer.full_name if banding.customer else "Anonim"
            income_map[(c_id, c_name)] += Decimal(str(banding.covered_amount))

        for cutting in Cutting.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            covered_amount__gt=0,
        ).select_related("customer"):
            c_id = cutting.customer.id if cutting.customer else None
            c_name = cutting.customer.full_name if cutting.customer else "Anonim"
            income_map[(c_id, c_name)] += Decimal(str(cutting.covered_amount))

        for payment in BalanceHistory.objects.filter(
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            type=BalanceHistory.Type.PAYMENT,
            amount__gt=0,
        ).select_related("customer"):
            c_id = payment.customer.id if payment.customer else None
            c_name = payment.customer.full_name if payment.customer else "Anonim"
            income_map[(c_id, c_name)] += Decimal(str(payment.amount))

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

        outcome = []
        outcome_total = Decimal("0")

        for item in expenses:
            outcome.append({
                "id": item.id,
                "type": "expense",
                "description": item.description,
                "date": item.created_at.strftime("%d.%m.%Y"),
                "value": item.value,
            })

            outcome_total += Decimal(str(item.value))

        for payment in supplier_payments:
            outcome.append({
                "id": payment.id,
                "type": "supplier_payment",
                "description": f"Supplier payment - {payment.supplier.full_name}",
                "date": payment.created_at.strftime("%d.%m.%Y"),
                "value": payment.amount,
            })

            outcome_total += Decimal(str(payment.amount))

        return {
            "from": str(start_date),
            "to": str(end_date),
            "income": income,
            "income_total": income_total,
            "expenses": expense_data,
            "expense_total": expense_total,
            "outcome": outcome,
            "outcome_total": outcome_total,
            "opening_balance": Decimal(
                str(
                    DashboardStatsService._cashbox_total(
                        end_dt=start_dt - timedelta(microseconds=1)
                    )
                )
            ),

            "closing_balance": Decimal(
                str(
                    DashboardStatsService._cashbox_total(end_dt=end_dt)
                )
            ),
        }