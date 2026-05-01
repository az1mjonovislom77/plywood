from decimal import Decimal, ROUND_HALF_UP
import requests

from django.core.management.base import BaseCommand
from acceptance.models import CurrencyRate
from order.models import OrderItem


class Command(BaseCommand):
    def get_rate(self, d):
        obj = CurrencyRate.objects.filter(date=d).first()
        if obj:
            return obj.rate

        url = f"https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/{d.strftime('%Y-%m-%d')}/"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        rate = Decimal(r.json()[0]["Rate"])

        CurrencyRate.objects.update_or_create(date=d, defaults={"rate": rate})
        return rate

    def handle(self, *args, **kwargs):
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

        self.stdout.write("done")