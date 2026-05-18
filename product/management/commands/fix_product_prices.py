from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance

class Command(BaseCommand):
    help = "Fixes product and acceptance prices (direct copy of arrival/sale prices)."

    def handle(self, *args, **options):
        self.stdout.write("1-bosqich: Acceptance jadvalidagi narxlarni to'g'rilash boshlandi...")
        
        # 1. Barcha Acceptance'larni to'g'rilash
        acceptances = Acceptance.objects.all()
        for acc in acceptances:
            acc.arrival_price_in_dollar = acc.arrival_price
            acc.sale_price_in_dollar = acc.sale_price
            acc.save(update_fields=['arrival_price_in_dollar', 'sale_price_in_dollar'])
            
        self.stdout.write(self.style.SUCCESS("Acceptance jadvali to'g'rilandi."))

        self.stdout.write("2-bosqich: Product jadvalidagi narxlarni to'g'rilash boshlandi...")
        # 2. Product'larni oxirgi Acceptance'ga qarab to'g'rilash
        products = Product.objects.all()
        updated_count = 0

        for product in products:
            last_acceptance = Acceptance.objects.filter(
                product=product,
                acceptance_status=Acceptance.AcceptanceStatus.ACCEPT
            ).order_by('-accepted_at').first()

            if last_acceptance:
                product.arrival_price = last_acceptance.arrival_price
                product.sale_price = last_acceptance.sale_price
                product.save(update_fields=['arrival_price', 'sale_price'])
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Bajarildi! Jami {updated_count} ta mahsulot narxi tiklandi."))