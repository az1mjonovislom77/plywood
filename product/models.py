from django.db import models
from django.utils import timezone
from category.models import Category
from product.utils import check_image_size
from django.core.validators import FileExtensionValidator


class Quality(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    class Quality(models.TextChoices):
        STANDARD = 'standard', "Standard"
        ECONOMIC = 'economic', "Economic"
        PREMIUM = 'premium', "Premium"

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200, db_index=True)
    color = models.CharField(max_length=200, null=True, blank=True)
    quality = models.CharField(choices=Quality.choices, default=Quality.STANDARD, max_length=20, db_index=True)
    image = models.ImageField(upload_to='product/', validators=[
        FileExtensionValidator(
            allowed_extensions=['jpg', 'jpeg', 'png', 'svg', 'webp', 'JPG', 'JPEG', 'PNG', 'SVG', 'WEBP']),
        check_image_size], blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    thick = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrival_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    arrival_price_in_dollar = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    count = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    arrival_date = models.DateField(default=timezone.localdate)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    @property
    def investment_in_dollar(self):
        if self.count and self.arrival_price_in_dollar:
            return self.count * self.arrival_price_in_dollar
        return 0

    def save(self, *args, **kwargs):
        from acceptance.models import CurrencyRate
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
        ordering = ['-id']

    def __str__(self):
        return self.name
