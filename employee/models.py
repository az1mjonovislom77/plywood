from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Employee(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.full_name


class SalaryPayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="salary_payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-paid_at"]         

    def __str__(self):
        return f"{self.employee.full_name} - {self.amount}"
