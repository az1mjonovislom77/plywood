from django.db import models
from django.utils import timezone
from category.models import Category


class Product(models.Model):
    class Quality(models.TextChoices):
        STANDARD = 'standard', "Standard"
        ECONOMIC = 'economic', "Economic"
        PREMIUM = 'premium', "Premium"

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200, db_index=True)
    color = models.CharField(max_length=200, null=True, blank=True)
    quality = models.CharField(choices=Quality.choices, default=Quality.STANDARD, max_length=20, db_index=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    thick = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.PositiveIntegerField(default=0)
    arrival_date = models.DateField(default=timezone.now)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.name
