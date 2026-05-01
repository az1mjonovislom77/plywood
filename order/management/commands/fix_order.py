from decimal import Decimal, ROUND_HALF_UP
import requests

from django.core.management.base import BaseCommand

from acceptance.models import CurrencyRate
from order.models import OrderItem


class Command(BaseCommand):
    help = "Fix old order item rates by order date"

    def get_rate(self, d):
        obj = CurrencyRate.objects.filter(date=d).first()
        if obj:
            return obj.rate

        url = f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/{d}/"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()[0]
        rate = Decimal(data["Rate"])

        CurrencyRate.objects.create(date=d, rate=rate)
        return rate

    def handle(self, *args, **options):
        items = OrderItem.objects.filter(exchange_rate__isnull=True)

        for item in items:
            d = item.order.created_at.date()
            rate = self.get_rate(d)

            item.exchange_rate = rate
            item.price_in_dollar = (item.price / rate).quantize(
                Decimal("0.0001"),
                rounding=ROUND_HALF_UP
            )
            item.save(update_fields=["exchange_rate", "price_in_dollar"])

        self.stdout.write(self.style.SUCCESS("Done"))