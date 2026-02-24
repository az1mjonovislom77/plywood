from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import F
from django.core.exceptions import ValidationError
from product.models import Product
from .models import Acceptance, AcceptanceHistory, CurrencyRate


@receiver(post_save, sender=Acceptance)
def handle_acceptance_create(sender, instance, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        AcceptanceHistory.objects.create(
            acceptance=instance,
            product=instance.product,
            arrival_price=instance.arrival_price,
            sale_price=instance.sale_price,
            count=instance.count,
            arrival_date=instance.arrival_date,
            description=instance.description,
        )

        arrival_price = instance.arrival_price
        sale_price = instance.sale_price

        if instance.price_type == Acceptance.PriceType.DOLLAR:
            rate = CurrencyRate.objects.filter(date__lte=instance.arrival_date).order_by("-date").first()

            if not rate:
                raise ValidationError("Dollar rate not found")

            arrival_price = (arrival_price * rate.rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            sale_price = (sale_price * rate.rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        Product.objects.filter(id=instance.product.id).update(
            count=F("count") + instance.count,
            arrival_price=arrival_price,
            sale_price=sale_price
        )
