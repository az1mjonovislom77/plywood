from django.db.models import Count, Q
from django.db.models.functions import Coalesce
from customer.models import Customer
from django.db.models import Sum, Value


class CustomerStatsService:

    @staticmethod
    def dashboard():
        stats = Customer.objects.aggregate(
            total_customers=Count("id"),
            debtor_customers=Count("id", filter=Q(debt__gt=0)),
            total_debt=Coalesce(Sum("debt"), Value(0))
        )

        return stats
