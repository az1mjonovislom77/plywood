from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import F
from django.core.exceptions import ValidationError
from product.models import Product
from supplier.models import Supplier, SupplierTransaction
from .models import Acceptance, AcceptanceHistory, CurrencyRate


@receiver(post_save, sender=Acceptance)
def handle_acceptance_create(sender, instance, created, **kwargs):
    if not created:
        return

    with transaction.atomic():

        rate_value = None

        if instance.price_type == Acceptance.PriceType.DOLLAR:
            rate = CurrencyRate.objects.filter(date__lte=instance.arrival_date).order_by("-date").first()

            if not rate:
                raise ValidationError("Dollar rate not found")

            rate_value = rate.rate

        AcceptanceHistory.objects.create(
            acceptance=instance,
            supplier=instance.supplier,
            product=instance.product,
            arrival_price=instance.arrival_price,
            sale_price=instance.sale_price,
            price_type=instance.price_type,
            exchange_rate=rate_value,
            count=instance.count,
            arrival_date=instance.arrival_date,
            description=instance.description,
        )

        arrival_price = instance.arrival_price
        sale_price = instance.sale_price

        if rate_value is not None:
            arrival_price = (arrival_price * rate_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            sale_price = (sale_price * rate_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        Product.objects.filter(pk=instance.product_id).update(count=F("count") + instance.count,
                                                              arrival_price=arrival_price,
                                                              sale_price=sale_price)

        total_amount = arrival_price * instance.count

        if instance.supplier_id:
            Supplier.objects.filter(pk=instance.supplier_id).update(debt=F("debt") + total_amount)

            SupplierTransaction.objects.create(
                supplier_id=instance.supplier_id,
                transaction_type=SupplierTransaction.TransactionType.PURCHASE,
                amount=total_amount,
                description=f"Acceptance #{instance.id}"
            )
