import logging
from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from employee.models import Employee, SalaryPayment
from user.models import User

logger = logging.getLogger(__name__)


class PaySalaryService:

    @staticmethod
    @transaction.atomic
    def pay_salary(employee_id: int, amount: Decimal, paid_by: User) -> SalaryPayment:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        employee = get_object_or_404(Employee, pk=employee_id)
        payment = SalaryPayment.objects.create(employee=employee, amount=amount, paid_by=paid_by)
        logger.info("Salary paid: employee %s, amount %s, by user %s", employee_id, amount, paid_by.id)
        return payment
