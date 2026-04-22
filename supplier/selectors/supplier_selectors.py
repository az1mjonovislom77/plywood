from decimal import Decimal
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from supplier.models import Supplier, SupplierTransaction


class SupplierSelector:
    @staticmethod
    def debt_stats():
        stats = Supplier.objects.aggregate(
            total_customers=Count("id"),
            total_debt=Coalesce(Sum("debt"), Decimal("0.00")),
        )

        return {
            "total_customers": stats["total_customers"],
            "total_debt": stats["total_debt"],
        }

    @staticmethod
    def suppliers_with_daily_acceptance_stats(date):
        investment_expr = ExpressionWrapper(
            F("acceptances__arrival_price") * F("acceptances__count"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        date_filter = Q(acceptances__created_at__date=date)

        return Supplier.objects.annotate(
            daily_acceptance_count=Coalesce(
                Sum("acceptances__count", filter=date_filter), Decimal("0"),
                output_field=DecimalField(max_digits=14, decimal_places=3),
            ),
            daily_investment=Coalesce(
                Sum(investment_expr, filter=date_filter), Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

    @staticmethod
    def transactions_with_stats(supplier_id):
        supplier = get_object_or_404(Supplier, id=supplier_id)
        transactions = supplier.transactions.all()

        total_purchases = transactions.filter(
            transaction_type=SupplierTransaction.TransactionType.PURCHASE
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))["total"]

        total_paid = transactions.filter(
            transaction_type=SupplierTransaction.TransactionType.PAYMENT
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0.00")))["total"]

        stats = {
            "total_purchases": total_purchases,
            "total_paid": total_paid,
            "remaining_debt": total_purchases - total_paid,
        }

        return supplier, transactions, stats
