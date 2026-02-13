from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import F
from product.models import Product
from .models import Acceptance, AcceptanceHistory


@receiver(post_save, sender=Acceptance)
def create_acceptance_history(sender, instance, created, **kwargs):
    if not created:
        return

    AcceptanceHistory.objects.create(
        acceptance=instance,
        product=instance.product,
        arrival_price=instance.arrival_price,
        sale_price=instance.sale_price,
        count=instance.count,
        arrival_date=instance.arrival_date,
        description=instance.description,
    )


@receiver(post_save, sender=Acceptance)
def update_product_on_acceptance_create(sender, instance, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        product = instance.product
        Product.objects.filter(id=product.id).update(count=F('count') + instance.count)

        if instance.arrival_price and instance.arrival_price > 0:
            Product.objects.filter(id=product.id).update(arrival_price=instance.arrival_price)

        if instance.sale_price and instance.sale_price > 0:
            Product.objects.filter(id=product.id).update(
                sale_price=instance.sale_price)
