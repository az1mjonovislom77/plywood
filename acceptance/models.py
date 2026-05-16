from django.db import models
from django.utils import timezone
from product.models import Product
from supplier.models import Supplier
from user.models import User


class CurrencyRate(models.Model):
    date = models.DateField(unique=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.rate}"


class Acceptance(models.Model):
    class PriceType(models.TextChoices):
        DOLLAR = "dollar", "Dollar"
        SUM = "sum", "Sum"

    class AcceptanceStatus(models.TextChoices):
        ACCEPT = "accept", "Accept"
        WAITING = "waiting", "Waiting"
        CANCEL = "cancel", "Cancel"

    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptances")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, related_name="acceptances", null=True, blank=True)
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrival_price_in_dollar = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrival_price_in_sum = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price_in_sum = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    price_type = models.CharField(max_length=10, choices=PriceType.choices, default=PriceType.SUM)
    count = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    acceptance_status = models.CharField(max_length=10, choices=AcceptanceStatus.choices,
                                         default=AcceptanceStatus.WAITING)
    accepted_by = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="accepted_acceptances")
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrival_date = models.DateField(default=timezone.localdate)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def save(self, *args, **kwargs):
        if self.price_type == self.PriceType.DOLLAR:
            self.arrival_price_in_dollar = self.arrival_price
            
            try:
                rate = CurrencyRate.objects.get(date=self.arrival_date).rate
                if rate and rate > 0:
                    self.arrival_price_in_sum = self.arrival_price * rate
                    self.sale_price_in_sum = self.sale_price * rate
                else:
                    self.arrival_price_in_sum = 0
                    self.sale_price_in_sum = 0
            except CurrencyRate.DoesNotExist:
                self.arrival_price_in_sum = 0
                self.sale_price_in_sum = 0
        else:
            self.arrival_price_in_sum = self.arrival_price
            self.sale_price_in_sum = self.sale_price

            try:
                rate = CurrencyRate.objects.get(date=self.arrival_date).rate
                if rate and rate > 0:
                    self.arrival_price_in_dollar = self.arrival_price / rate
                else:
                    self.arrival_price_in_dollar = 0
            except CurrencyRate.DoesNotExist:
                self.arrival_price_in_dollar = 0
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.product.name}"


class AcceptanceHistory(models.Model):
    class PriceTypeChoice(models.TextChoices):
        DOLLAR = "dollar", "Dollar"
        SUM = "sum", "Sum"

    class Action(models.TextChoices):
        CREATE = "create", "Create"
        ACCEPT = "accept", "Accept"
        CANCEL = "cancel", "Cancel"

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    acceptance = models.ForeignKey(Acceptance, on_delete=models.CASCADE, related_name='histories')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="acceptance_histories")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptance_histories")
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    price_type = models.CharField(max_length=10, choices=PriceTypeChoice.choices)
    action = models.CharField(max_length=20, choices=Action.choices)
    count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.product.name}"