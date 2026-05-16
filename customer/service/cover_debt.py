from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from customer.models import Customer, BalanceHistory
from customer.service.customer_balance import CustomerBalanceService


class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount):

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = Customer.objects.select_for_update().get(pk=customer_id)

        Customer.objects.filter(pk=customer_id).update(
            debt=F("debt") - amount,
            covered_debt=F("covered_debt") + amount
        )

        BalanceHistory.objects.create(
            customer=customer,
            type=BalanceHistory.Type.PAYMENT,
            amount=amount
        )

        customer.refresh_from_db()

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