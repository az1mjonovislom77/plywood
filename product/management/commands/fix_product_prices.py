from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance
from decimal import Decimal, ROUND_HALF_UP

def are_decimals_equal(d1, d2, precision='0.01'):
    if d1 is None and d2 is None: return True
    if d1 is None or d2 is None: return False
    quantizer = Decimal(precision)
    return d1.quantize(quantizer) == d2.quantize(quantizer)

class Command(BaseCommand):
    help = "Fixes product prices based on the last 'ACCEPT' status acceptance."

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix product prices based on the new model structure...")

        products = Product.objects.all()
        updated_count = 0
        checked_count = 0

        for product in products:
            checked_count += 1
            last_acceptance = Acceptance.objects.filter(
                product=product,
                acceptance_status=Acceptance.AcceptanceStatus.ACCEPT
            ).order_by('-accepted_at').first()

            if not last_acceptance:
                continue

            update_fields = []
            
            # Product.arrival_price (USD) ni Acceptance.arrival_price_in_dollar bilan solishtirish
            if not are_decimals_equal(product.arrival_price, last_acceptance.arrival_price_in_dollar):
                product.arrival_price = last_acceptance.arrival_price_in_dollar
                update_fields.append('arrival_price')

            # Product.sale_price (USD) ni Acceptance.sale_price_in_dollar bilan solishtirish
            if not are_decimals_equal(product.sale_price, last_acceptance.sale_price_in_dollar):
                product.sale_price = last_acceptance.sale_price_in_dollar
                update_fields.append('sale_price')

            # Product.arrival_price_in_sum ni Acceptance.arrival_price_in_sum bilan solishtirish
            if not are_decimals_equal(product.arrival_price_in_sum, last_acceptance.arrival_price_in_sum):
                product.arrival_price_in_sum = last_acceptance.arrival_price_in_sum
                update_fields.append('arrival_price_in_sum')

            # Product.sale_price_in_sum ni Acceptance.sale_price_in_sum bilan solishtirish
            if not are_decimals_equal(product.sale_price_in_sum, last_acceptance.sale_price_in_sum):
                product.sale_price_in_sum = last_acceptance.sale_price_in_sum
                update_fields.append('sale_price_in_sum')

            if update_fields:
                product.save(update_fields=update_fields)
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated prices for '{product.name}' (ID: {product.id})"))

        self.stdout.write(self.style.SUCCESS(
            f"Finished fixing prices. Products checked: {checked_count}. Total products updated: {updated_count}"
        ))