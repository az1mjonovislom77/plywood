from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError

from customer.models import Customer, BalanceHistory
from customer.service.statement_service import CustomerStatementService


class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount):

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = Customer.objects.select_for_update().get(pk=customer_id)

        Customer.objects.filter(pk=customer_id).update(
            debt=F("debt") - amount,
            covered_debt=F("covered_debt") + amount,
        )

        BalanceHistory.objects.create(
            customer=customer,
            type=BalanceHistory.Type.PAYMENT,
            amount=amount
        )

        customer.refresh_from_db()
        return customer

    @staticmethod
    def get_customer_history(customer_id):

        statement = CustomerStatementService.build_statement(
            customer_id=customer_id
        )

        history = []

        for row in statement["rows"]:

            if row["income_amount"]:

                history.append({
                    "type": "PAYMENT",
                    "amount": row["income_amount"],
                    "created_at": row["date"],
                })

            elif row["expense_amount"]:

                history.append({
                    "type": "DEBT_ADD",
                    "amount": row["expense_amount"],
                    "created_at": row["date"],
                })

        history = sorted(
            history,
            key=lambda x: x["created_at"],
            reverse=True
        )

        return {
            "history": history,
            "stats": {
                "total_orders": statement["totals"]["expense_amount"],
                "total_paid": statement["totals"]["income_amount"],
                "remaining_debt": max(
                    -statement["totals"]["closing_balance"],
                    0
                ),
            }
        }
