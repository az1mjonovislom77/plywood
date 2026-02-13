from django.db import models
from product.models import Product
from user.models import User


class Basket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="baskets")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"], condition=models.Q(is_active=True),
                                    name="unique_active_basket_per_user")]


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("basket", "product")


class Thickness(models.Model):
    size = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.size)


class Banding(models.Model):
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    meter = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.width)


class Cutting(models.Model):
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.count)
