from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=100, db_index=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, db_index=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    about = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return self.full_name
