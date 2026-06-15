from decimal import Decimal
from django.test import TestCase
from employee.models import Employee
from employee.service.pay_salary import PaySalaryService
from user.models import User


class PaySalaryServiceTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager", password="123", role=User.UserRoles.MANAGER)
        self.employee = Employee.objects.create(full_name="Test Employee")

    def test_pay_salary_creates_payment_record(self):
        payment = PaySalaryService.pay_salary(self.employee.id, Decimal("1500000.00"), self.manager)
        self.assertEqual(payment.amount, Decimal("1500000.00"))
        self.assertEqual(payment.employee, self.employee)
        self.assertEqual(payment.paid_by, self.manager)

    def test_pay_salary_rejects_zero_amount(self):
        with self.assertRaises(ValueError):
            PaySalaryService.pay_salary(self.employee.id, Decimal("0"), self.manager)

    def test_pay_salary_rejects_negative_amount(self):
        with self.assertRaises(ValueError):
            PaySalaryService.pay_salary(self.employee.id, Decimal("-100"), self.manager)
