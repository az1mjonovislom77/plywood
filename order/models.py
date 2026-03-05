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
        constraints = [models.UniqueConstraint(
            fields=["user"], condition=models.Q(is_active=True),
            name="unique_active_basket_per_user")]


class BasketItem(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["basket", "product"], name="unique_product_per_basket")]


class Thickness(models.Model):
    text = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.text)


class Banding(models.Model):
    thickness = models.ForeignKey("Thickness", on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="bandings")
    length = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def calculate_price(self):
        if self.thickness:
            return self.length * self.thickness.price
        return Decimal("0")

    def __str__(self):
        return f"{self.length}"


class Cutting(models.Model):
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

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

    class OrderSource(models.TextChoices):
        SELLER = "seller", "Seller"
        CASHIER = "cashier", "Cashier"

    class OrderStatus(models.TextChoices):
        ACCEPT = "accept", "Accept"
        WAITING = "waiting", "Waiting"
        CANCEL = "cancel", "Cancel"

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    customer = models.ForeignKey("customer.Customer", on_delete=models.PROTECT, related_name="orders", null=True,
                                 blank=True)
    is_anonymous = models.BooleanField(default=True)
    source = models.CharField(max_length=10, choices=OrderSource.choices, default=OrderSource.SELLER)
    order_status = models.CharField(max_length=10, choices=OrderStatus.choices, default=OrderStatus.WAITING)
    accepted_by = models.ForeignKey("user.User", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="accepted_orders")
    accepted_at = models.DateTimeField(null=True, blank=True)
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

        if not self.pk:
            return

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

        total = max(total, Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if self.covered_amount > total:
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


class OrderHistory(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        ACCEPT = "accept", "Accept"
        CANCEL = "cancel", "Cancel"
        UPDATE = "update", "Update"

    class VisibleFor(models.TextChoices):
        SELLER = "seller", "Seller"
        CASHIER = "cashier", "Cashier"

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="history")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    visible_for = models.CharField(max_length=10, choices=VisibleFor.choices)
    description = models.TextField(blank=True, null=True, max_length=500)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
