from django.db import transaction
from django.db.models import F, Sum
from django.core.exceptions import ValidationError

from customer.models import Customer, BalanceHistory
from order.models import Order


class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount):

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = Customer.objects.select_for_update().get(pk=customer_id)
        if amount > customer.debt:
            raise ValidationError("Amount exceeds debt")

        Customer.objects.filter(pk=customer_id).update(debt=F("debt") - amount)
        BalanceHistory.objects.create(customer=customer, type=BalanceHistory.Type.PAYMENT, amount=amount)

        customer.refresh_from_db()
        return customer

    @staticmethod
    def get_customer_history(customer_id: int):
        customer = Customer.objects.get(pk=customer_id)

        history_qs = BalanceHistory.objects.filter(customer_id=customer_id).order_by("-created_at")
        total_orders = (Order.objects.filter(customer_id=customer_id).aggregate(total=Sum("total_price"))["total"] or 0)
        total_paid = (BalanceHistory.objects
                      .filter(customer_id=customer_id, type=BalanceHistory.Type.PAYMENT)
                      .aggregate(total=Sum("amount"))["total"] or 0)

        return {
            "history": history_qs,
            "stats": {
                "total_orders": total_orders,
                "total_paid": total_paid,
                "remaining_debt": customer.debt
            }
        }
