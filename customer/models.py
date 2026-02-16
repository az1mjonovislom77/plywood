from django.db import models
from django.db.models import F
from django.core.exceptions import ValidationError
from decimal import Decimal


class Customer(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    debt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    about = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def clean(self):
        if self.debt < Decimal("0"):
            raise ValidationError("Debt cannot be negative")

    def increase_debt(self, amount):
        if amount <= 0:
            return

        Customer.objects.filter(id=self.id).update(debt=F("debt") + amount)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.full_name
