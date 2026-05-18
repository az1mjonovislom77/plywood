from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance


class Command(BaseCommand):
    help = "Fixes the arrival and sale prices (in UZS and USD) for all products based on the last acceptance"

    def handle(self, *args, **options):
        self.stdout.write("Starting to fix product prices...")

        products = Product.objects.all()
        updated_count = 0

        for product in products:
            last_acceptance = Acceptance.objects.filter(
                product=product,
                acceptance_status=Acceptance.AcceptanceStatus.ACCEPT
            ).order_by('-accepted_at').first()

            if last_acceptance:
                update_fields = []
                
                # Dollar kelish narxini to'g'irlash
                if product.arrival_price_in_dollar != last_acceptance.arrival_price_in_dollar:
                    product.arrival_price_in_dollar = last_acceptance.arrival_price_in_dollar
                    update_fields.append('arrival_price_in_dollar')
                
                # So'mdagi kelish narxini to'g'irlash
                if product.arrival_price != last_acceptance.arrival_price_in_sum:
                    product.arrival_price = last_acceptance.arrival_price_in_sum
                    update_fields.append('arrival_price')

                # Dollar sotish narxini to'g'irlash
                if product.sale_price_in_dollar != last_acceptance.sale_price_in_dollar:
                    product.sale_price_in_dollar = last_acceptance.sale_price_in_dollar
                    update_fields.append('sale_price_in_dollar')

                # So'mdagi sotish narxini to'g'irlash
                if product.sale_price != last_acceptance.sale_price_in_sum:
                    product.sale_price = last_acceptance.sale_price_in_sum
                    update_fields.append('sale_price')

                if update_fields:
                    product.save(update_fields=update_fields)
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Updated prices for '{product.name}' (ID: {product.id}). "
                        f"Arrival $: {product.arrival_price_in_dollar}, Sale $: {product.sale_price_in_dollar}, "
                        f"Arrival UZS: {product.arrival_price}, Sale UZS: {product.sale_price}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"Finished fixing prices. Total products updated: {updated_count}"
        ))