from decimal import Decimal, ROUND_HALF_UP
from django.core.exceptions import ValidationError
from django.db import models
from user.models import User


class Currency(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class NotificationSettings(models.Model):
    low_stock_threshold = models.PositiveIntegerField(default=20)

    class Meta:
        verbose_name = "Notification Settings"
        verbose_name_plural = "Notification Settings"

    def __str__(self):
        return str(self.low_stock_threshold)


class Expenses(models.Model):
    class ExpensesStatus(models.TextChoices):
        ACCEPT = "accept", "Accept"
        WAITING = "waiting", "Waiting"
        CANCEL = "cancel", "Cancel"
        CREATED = "created", "Created"
    class ExpensesType(models.TextChoices):
        ZAVOD = "Zavod", "Zavod"
        BOSHQA = "Boshqa", "Boshqa"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(choices=ExpensesType.choices, default=ExpensesType.BOSHQA, max_length=10)
    value = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200)
    expense_status = models.CharField(choices=ExpensesStatus.choices, default=ExpensesStatus.ACCEPT, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user)


class ExpensesHistory(models.Model):
    class Action(models.TextChoices):
        CREATE = "created", "Created"
        ACCEPT = "accept", "Accept"
        CANCEL = "cancel", "Cancel"

    expense = models.ForeignKey(Expenses, on_delete=models.CASCADE, related_name="histories")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=Action.choices)
    value = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.expense)


class ServicesName(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Services(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = "p", "Foiz"
        CASH = "c", "Naqd"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Naqd"
        CARD = "card", "Kart"
        NASIYA = "nasiya", "Nasiya"

    services_name = models.ForeignKey(ServicesName, on_delete=models.CASCADE, related_name="services")
    customer = models.ForeignKey("customer.Customer", on_delete=models.PROTECT, related_name="services", null=True,
                                 blank=True)
    description = models.TextField(blank=True, null=True)
    count = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=20, decimal_places=3)
    total_price = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    discount_type = models.CharField(choices=DiscountType.choices, max_length=1, default=DiscountType.CASH)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(choices=PaymentMethod.choices, max_length=20, default=PaymentMethod.CASH)
    covered_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_price(self):
        return Decimal(self.count) * self.price

    def clean(self):
        if self.covered_amount < 0:
            raise ValidationError("To'langan summa manfiy bo'lishi mumkin emas")

        total = self.calculate_price().quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if self.covered_amount > total:
            raise ValidationError("To'langan summa umumiy narxdan oshmasligi kerak")

    def __str__(self):
        return str(self.services_name)
