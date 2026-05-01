from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from acceptance.models import CurrencyRate
from order.models import OrderItem


class Command(BaseCommand):
    help = "Fix null exchange_rate and price_in_dollar in old order items"

    def handle(self, *args, **options):
        items = OrderItem.objects.filter(exchange_rate__isnull=True)

        fixed = 0
        skipped = 0

        for item in items:
            order_date = item.order.created_at.date()

            rate_obj = CurrencyRate.objects.filter(date=order_date).first()
            if not rate_obj:
                rate_obj = (
                    CurrencyRate.objects
                    .filter(date__lte=order_date)
                    .order_by("-date")
                    .first()
                )

            if not rate_obj:
                skipped += 1
                continue

            item.exchange_rate = rate_obj.rate
            item.price_in_dollar = (item.price / rate_obj.rate).quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP
            )
            item.save(update_fields=["exchange_rate", "price_in_dollar"])
            fixed += 1

        self.stdout.write(self.style.SUCCESS(f"Fixed: {fixed}, Skipped: {skipped}"))