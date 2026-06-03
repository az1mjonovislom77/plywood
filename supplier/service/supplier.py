from django.db import transaction
from django.core.exceptions import ValidationError
from supplier.models import Supplier, SupplierTransaction
from utils.service.comprehensive_stats import DashboardStatsService
from django.db.models import Sum, Case, When, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal


class SupplierService:

    @staticmethod
    def recalculate_debt(supplier):
        debt = supplier.transactions.aggregate(
            total=Coalesce(
                Sum(
                    Case(
                        When(transaction_type="purchase", then=F("amount")),
                        When(transaction_type="payment", then=F("amount") * Decimal("-1")),
                        default=Decimal("0.00"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )), Decimal("0.00")))["total"]

        supplier.debt = debt
        supplier.save(update_fields=["debt"])

        return supplier

    @staticmethod
    @transaction.atomic
    def make_payment(supplier_id, amount):
        supplier = Supplier.objects.select_for_update().get(id=supplier_id)

        supplier = SupplierService.recalculate_debt(supplier)

        if amount <= 0:
            raise ValidationError("Payment must be positive")

        if amount > supplier.debt:
            raise ValidationError("Payment exceeds current debt")

        stats = DashboardStatsService.get_stats()
        if amount > stats["cashbox_total"]:
            raise ValidationError("Payment exceeds current cashbox balance")

        SupplierTransaction.objects.create(
            supplier=supplier, transaction_type=SupplierTransaction.TransactionType.PAYMENT,
            amount=amount, description="Debt payment"
        )

        SupplierService.recalculate_debt(supplier)

        return supplier
