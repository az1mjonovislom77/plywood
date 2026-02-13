from django.db import models
from django.utils import timezone
from product.models import Product


class Acceptance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptances")
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.PositiveIntegerField(default=0)
    arrival_date = models.DateField(default=timezone.now)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.product.name}"


class AcceptanceHistory(models.Model):
    acceptance = models.OneToOneField('warehouse.Acceptance', on_delete=models.CASCADE, related_name='history')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="acceptance_histories")
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    count = models.PositiveIntegerField()
    arrival_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.product.name}"
