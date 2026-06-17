import logging
from django.db import transaction
from django.core.exceptions import ValidationError
from supplier.models import Supplier, SupplierTransaction
from utils.service.comprehensive_stats import DashboardStatsService
from django.db.models import Sum, Case, When, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

logger = logging.getLogger(__name__)


class SupplierService:

    @staticmethod
    def recalculate_debt(supplier):
        net = supplier.transactions.aggregate(
            total=Coalesce(
                Sum(
                    Case(
                        When(transaction_type="purchase", then=F("amount")),
                        When(transaction_type="payment", then=F("amount") * Decimal("-1")),
                        default=Decimal("0.00"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )), Decimal("0.00")))["total"]

        supplier.debt = max(net, Decimal("0"))
        supplier.overpayment = max(-net, Decimal("0"))
        supplier.save(update_fields=["debt", "overpayment"])

        return supplier

    @staticmethod
    @transaction.atomic
    def make_payment(supplier_id: int, amount: Decimal) -> Supplier:
        supplier = Supplier.objects.select_for_update().get(id=supplier_id)

        if amount <= 0:
            raise ValidationError("To'lov musbat bo'lishi kerak")

        stats = DashboardStatsService.get_stats()
        if amount > stats["cashbox_total"]:
            raise ValidationError("To'lov joriy kassa qoldiqidan oshib ketdi")

        SupplierTransaction.objects.create(
            supplier=supplier, transaction_type=SupplierTransaction.TransactionType.PAYMENT,
            amount=amount, description="Debt payment"
        )

        SupplierService.recalculate_debt(supplier)
        logger.info("Supplier #%s payment: %s", supplier_id, amount)
        return supplier
