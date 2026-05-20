from django.db import transaction

from employee.models import Employee


class PaySalaryService:

    @staticmethod
    @transaction.atomic
    def pay_salary(employee_id: int, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")

        employee = Employee.objects.select_for_update().get(pk=employee_id)

