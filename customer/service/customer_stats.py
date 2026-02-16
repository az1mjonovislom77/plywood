from decimal import Decimal
from django.db.models import Count, Q, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from customer.models import Customer


class CustomerStatsService:

    @staticmethod
    def dashboard():
        stats = Customer.objects.aggregate(
            total_customers=Count("id"),
            debtor_customers=Count("id", filter=Q(debt__gt=0)),
            total_debt=Coalesce(Sum("debt"), Value(Decimal("0.00")), output_field=DecimalField())
        )

        return stats
