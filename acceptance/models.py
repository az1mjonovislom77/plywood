from django.db import models
from django.utils import timezone
from product.models import Product
from supplier.models import Supplier


class CurrencyRate(models.Model):
    date = models.DateField(unique=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.rate}"


class Acceptance(models.Model):
    class PriceType(models.TextChoices):
        DOLLAR = "dollar", "Dollar"
        SUM = "sum", "Sum"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptances")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="acceptances", null=True, blank=True)
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_type = models.CharField(max_length=10, choices=PriceType.choices, default=PriceType.SUM)
    count = models.PositiveIntegerField(default=0)
    arrival_date = models.DateField(default=timezone.now)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.product.name}"


class AcceptanceHistory(models.Model):
    class PriceTypeChoice(models.TextChoices):
        DOLLAR = "dollar", "Dollar"
        SUM = "sum", "Sum"

    acceptance = models.OneToOneField('Acceptance', on_delete=models.CASCADE, related_name='history')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="history")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptance_histories")
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    price_type = models.CharField(max_length=10, choices=PriceTypeChoice.choices)
    count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.product.name}"
