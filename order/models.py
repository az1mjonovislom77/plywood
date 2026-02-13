from django.db import models

from product.models import Product


class Basket(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return str(self.product.id)

#
# class Order(models.Model):
