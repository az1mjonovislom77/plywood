from decimal import Decimal
from django.db.models import Count, Q, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from customer.models import Customer
from order.models import Order


class CustomerStatsSelector:
    @staticmethod
    def dashboard_stats():
        return Customer.objects.aggregate(
            total_customers=Count("id"),
            debtor_customers=Count("id", filter=Q(debt__gt=0)),
            total_debt=Coalesce(
                Sum("debt", filter=Q(debt__gt=0)), Value(Decimal("0.00")),
                output_field=DecimalField(),
            ),
            total_overpayment=Coalesce(
                Sum("overpayment", filter=Q(overpayment__gt=0)), Value(Decimal("0.00")),
                output_field=DecimalField(),
            ),
        )
