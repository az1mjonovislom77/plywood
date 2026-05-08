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
            total_debt=Coalesce(Sum("debt"), Value(Decimal("0.00")), output_field=DecimalField()),
        )


class CustomerDebtSelector:
    @staticmethod
    def dashboard_debt_stats():
        customer_stats = Customer.objects.aggregate(
            total_debt=Coalesce(Sum("debt"), Decimal("0.00")),
            debtor_customers=Coalesce(Count("id", filter=Q(debt__gt=0)), 0),
        )

        nasiya_sales = Order.objects.filter(
            payment_method=Order.PaymentMethod.NASIYA
        ).exclude(order_status=Order.OrderStatus.CANCEL).count()

        return {
            "total_debt": customer_stats["total_debt"],
            "debtor_customers": customer_stats["debtor_customers"],
            "nasiya_sales": nasiya_sales,
        }
