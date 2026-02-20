from django.db.models import Sum, Count, Q
from django.db.models.functions import Coalesce
from decimal import Decimal

from customer.models import Customer
from order.models import Order


class DashboardStatsService:

    @staticmethod
    def get_debt_stats():
        customer_stats = Customer.objects.aggregate(
            total_debt=Coalesce(Sum("debt"), Decimal("0.00")),
            debtor_customers=Coalesce(Count("id", filter=Q(debt__gt=0)), 0))

        nasiya_sales = Order.objects.filter(payment_method=Order.PaymentMethod.NASIYA).count()

        return {
            "total_debt": customer_stats["total_debt"],
            "debtor_customers": customer_stats["debtor_customers"],
            "nasiya_sales": nasiya_sales
        }
