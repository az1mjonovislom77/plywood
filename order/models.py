from decimal import Decimal, ROUND_HALF_UP
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
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

    class Meta:
        unique_together = ("basket", "product")


class Thickness(models.Model):
    size = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.size)


class Banding(models.Model):
    thickness = models.ForeignKey("Thickness", on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="bandings")
    width = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    height = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def linear_meter(self):
        return (self.width + self.height) * Decimal("2")

    def calculate_price(self):
        if self.thickness:
            return self.linear_meter() * self.thickness.price

        return Decimal("0")

    def __str__(self):
        return f"{self.linear_meter()} m"


class Cutting(models.Model):
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def calculate_price(self):
        if self.count:
            return self.price * self.count
        return Decimal("0")

    def __str__(self):
        return str(self.count)


class Order(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "p", "Percentage"
        CASH = "c", "Cash"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        NASIYA = "nasiya", "Nasiya"
        MIXED = "mixed", "Mixed"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey("customer.Customer", on_delete=models.PROTECT, related_name="orders", null=True,
                                 blank=True)
    is_anonymous = models.BooleanField(default=False)
    discount_type = models.CharField(choices=DiscountType.choices, max_length=1, default=DiscountType.CASH)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(choices=PaymentMethod.choices, max_length=20, default=PaymentMethod.CASH)
    covered_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    banding = models.ForeignKey("Banding", on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    cutting = models.ForeignKey("Cutting", on_delete=models.SET_NULL, related_name="orders", null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order #{self.id}"

    def calculate_total(self):
        total = sum((item.price * item.quantity for item in self.items.all()), Decimal("0"))

        if self.banding:
            total += self.banding.calculate_price()
        if self.cutting:
            total += self.cutting.calculate_price()
        if self.discount > 0:
            if self.discount_type == self.DiscountType.PERCENTAGE:
                total -= total * (self.discount / Decimal("100"))
            else:
                total -= self.discount

        total = max(total, Decimal("0"))
        total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        self.total_price = total

    def clean(self):
        if self.covered_amount < 0:
            raise ValidationError("Covered amount cannot be negative")
        if self.covered_amount > self.total_price:
            raise ValidationError("Covered amount cannot exceed total price")


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("product.Product", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
