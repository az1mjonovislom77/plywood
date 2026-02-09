from django.db import models
from django.utils import timezone

from category.models import Category


class Product(models.Model):
    class Quality(models.TextChoices):
        STANDARD = 'standard', "Standard"
        ECONOMIC = 'economic', "Economic"
        PREMIUM = 'premium', "Premium"

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    color = models.CharField(max_length=200, null=True, blank=True)
    quality = models.CharField(choices=Quality.choices, default=Quality.STANDARD, max_length=20)
    width = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    thick = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    count = models.PositiveIntegerField(default=0)
    arrival_date = models.DateField(default=timezone.now)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name
