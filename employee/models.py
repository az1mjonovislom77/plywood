from django.db import models


class Employee(models.Model):
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    salary = models.DecimalField(max_digits=20, decimal_places=2)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name
