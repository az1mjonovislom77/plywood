from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError

from customer.models import Customer, Payment


class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount):

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = (Customer.objects.select_for_update().filter(pk=customer_id).first())

        if not customer:
            raise ValidationError("Customer not found")

        if amount > customer.debt:
            raise ValidationError("Amount exceeds debt")

        Customer.objects.filter(pk=customer_id).update(debt=F("debt") - amount, covered_debt=F("covered_debt") + amount)

        payment = Payment.objects.create(customer=customer, amount=amount)

        customer.refresh_from_db()

        return customer, payment
