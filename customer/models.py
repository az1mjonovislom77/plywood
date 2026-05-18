from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    covered_debt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overpayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    about = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def sync_debt(self):
        from customer.service.customer_balance import CustomerBalanceService
        debt = CustomerBalanceService.sync_customer_debt(self.id)

        self.refresh_from_db(fields=["debt"])

        return debt

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.full_name


class BalanceHistory(models.Model):
    class Type(models.TextChoices):
        DEBT_ADD = "DEBT_ADD", "Debt Added"
        PAYMENT = "PAYMENT", "Debt Payment"
        ORDER_PAYMENT = "ORDER_PAYMENT", "Order Payment"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="history")
    type = models.CharField(max_length=20, choices=Type.choices)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
