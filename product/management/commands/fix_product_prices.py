from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance


class Command(BaseCommand):
    help = "Fixes the arrival and sale prices (in UZS and USD) for all products based on the last acceptance"

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix product prices...")

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
                self.stdout.write(self.style.WARNING(f"No 'ACCEPT' status acceptance found for '{product.name}' (ID: {product.id}). Skipping."))
                continue

            self.stdout.write(f"--- Checking '{product.name}' (ID: {product.id}) ---")
            self.stdout.write(f"  Product prices: Arrival($)={product.arrival_price_in_dollar}, Sale($)={product.sale_price_in_dollar}, Arrival(UZS)={product.arrival_price}, Sale(UZS)={product.sale_price}")
            self.stdout.write(f"  Acceptance prices: Arrival($)={last_acceptance.arrival_price_in_dollar}, Sale($)={last_acceptance.sale_price_in_dollar}, Arrival(UZS)={last_acceptance.arrival_price_in_sum}, Sale(UZS)={last_acceptance.sale_price_in_sum}")

            update_fields = []
            
            if product.arrival_price_in_dollar != last_acceptance.arrival_price_in_dollar:
                self.stdout.write(f"  [CHANGE] Arrival price in dollar is different.")
                product.arrival_price_in_dollar = last_acceptance.arrival_price_in_dollar
                update_fields.append('arrival_price_in_dollar')
            
            if product.arrival_price != last_acceptance.arrival_price_in_sum:
                self.stdout.write(f"  [CHANGE] Arrival price in UZS is different.")
                product.arrival_price = last_acceptance.arrival_price_in_sum
                update_fields.append('arrival_price')

            if product.sale_price_in_dollar != last_acceptance.sale_price_in_dollar:
                self.stdout.write(f"  [CHANGE] Sale price in dollar is different.")
                product.sale_price_in_dollar = last_acceptance.sale_price_in_dollar
                update_fields.append('sale_price_in_dollar')

            if product.sale_price != last_acceptance.sale_price_in_sum:
                self.stdout.write(f"  [CHANGE] Sale price in UZS is different.")
                product.sale_price = last_acceptance.sale_price_in_sum
                update_fields.append('sale_price')

            if update_fields:
                product.save(update_fields=update_fields)
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Successfully updated prices for '{product.name}'."))
            else:
                self.stdout.write(self.style.NOTICE(f"  No price differences found. No update needed."))

        self.stdout.write("---" * 10)
        self.stdout.write(self.style.SUCCESS(
            f"Finished fixing prices. Products checked: {checked_count}. Total products updated: {updated_count}"
        ))