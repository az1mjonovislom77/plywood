from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance


class Command(BaseCommand):
    help = "Fixes the arrival_price_in_dollar for all products based on the last acceptance"

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
                if product.arrival_price_in_dollar != last_acceptance.arrival_price_in_dollar:
                    product.arrival_price_in_dollar = last_acceptance.arrival_price_in_dollar
                    product.save(update_fields=['arrival_price_in_dollar'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Updated price for '{product.name}' (ID: {product.id}) to ${product.arrival_price_in_dollar}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"Finished fixing prices. Total products updated: {updated_count}"
        ))
