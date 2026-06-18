import logging
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from customer.models import Customer, BalanceHistory
from customer.service.customer_balance import CustomerBalanceService

logger = logging.getLogger(__name__)


class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount: Decimal) -> Customer:

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = Customer.objects.select_for_update().get(pk=customer_id)

        paid_to_debt = min(amount, max(customer.debt, 0))
        overpayment = amount - paid_to_debt

        Customer.objects.filter(pk=customer_id).update(
            debt=F("debt") - paid_to_debt,
            covered_debt=F("covered_debt") + paid_to_debt,
            overpayment=F("overpayment") + overpayment,
        )

        BalanceHistory.objects.create(
            customer=customer,
            type=BalanceHistory.Type.PAYMENT,
            amount=amount
        )

        customer.refresh_from_db()
        logger.info("Debt covered: customer %s, amount %s", customer_id, amount)
        return customer

    @staticmethod
    @transaction.atomic
    def refund_overpayment(customer_id: int, amount: Decimal) -> Customer:
        if amount <= 0:
            raise ValidationError("Summa musbat bo'lishi kerak")

        customer = Customer.objects.select_for_update().get(pk=customer_id)

        from utils.service.comprehensive_stats import DashboardStatsService
        stats = DashboardStatsService.get_stats()
        if amount > Decimal(str(stats["cashbox_total"])):
            raise ValidationError("Kassa qoldig'i yetarli emas")

        BalanceHistory.objects.create(
            customer=customer,
            type=BalanceHistory.Type.REFUND,
            amount=amount
        )

        customer.sync_debt()
        logger.info("Refund: customer %s, amount %s", customer_id, amount)
        return customer

    @staticmethod
    def get_customer_history(customer_id: int):

        history_qs = (
            BalanceHistory.objects
            .filter(customer_id=customer_id)
            .order_by("-created_at")
        )

        stats = CustomerBalanceService.calculate(customer_id)

        return {
            "history": history_qs,
            "stats": {
                "total_orders": stats["total_orders"],
                "total_paid": stats["total_paid"],
                "remaining_debt": stats["remaining_debt"],
            }
        }
