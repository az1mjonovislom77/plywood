from django.db import models


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
