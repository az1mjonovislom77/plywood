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
    thickness = models.ForeignKey(Thickness, on_delete=models.SET_NULL, related_name="bandings", null=True, blank=True)
    width = models.DecimalField(max_digits=10, decimal_places=2)
    height = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.width)


class Cutting(models.Model):
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.count)


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="orders")
    banding = models.ForeignKey(Banding, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    cutting = models.ForeignKey(Cutting, on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.product.id)
