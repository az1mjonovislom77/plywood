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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200)
    expense_status = models.CharField(choices=ExpensesStatus.choices, default=ExpensesStatus.ACCEPT, max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.value)


class ExpensesHistory(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        ACCEPT = "accept", "Accept"
        CANCEL = "cancel", "Cancel"

    expense = models.ForeignKey(Expenses, on_delete=models.CASCADE, related_name="histories")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=Action.choices)
    value = models.PositiveIntegerField()
    description = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
