from django.db import transaction
from django.core.exceptions import ValidationError
from supplier.models import Supplier, SupplierTransaction
from utils.service.comprehensive_stats import DashboardStatsService


class SupplierService:

    @staticmethod
    @transaction.atomic
    def make_payment(supplier_id, amount):
        supplier = Supplier.objects.select_for_update().get(id=supplier_id)

        if amount <= 0:
            raise ValidationError("Payment must be positive")
        if amount > supplier.debt:
            raise ValidationError("Payment exceeds current debt")

        stats = DashboardStatsService.get_stats()
        if amount > stats["cashbox_total"]:
            raise ValidationError("Payment exceeds current cashbox balance")

        supplier.debt -= amount

        supplier.save(update_fields=["debt"])

        SupplierTransaction.objects.create(
            supplier=supplier,
            transaction_type=SupplierTransaction.TransactionType.PAYMENT, amount=amount, description="Debt payment")

        return supplier
