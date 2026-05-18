from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance, CurrencyRate
from decimal import Decimal

class Command(BaseCommand):
    help = "Fixes product and acceptance prices (direct copy of arrival/sale prices as DOLLAR)."

    def handle(self, *args, **options):
        self.stdout.write("1-bosqich: Acceptance jadvalidagi narxlarni to'g'rilash boshlandi...")
        
        # 1. Barcha Acceptance'larni to'g'rilash
        acceptances = Acceptance.objects.all()
        for acc in acceptances:
            # Acceptance'da kiritilgan narxlarni to'g'ridan-to'g'ri DOLLAR deb qabul qilamiz
            acc.arrival_price_in_dollar = acc.arrival_price
            acc.sale_price_in_dollar = acc.sale_price
            
            rate = CurrencyRate.objects.filter(date__lte=acc.arrival_date).order_by("-date").first()
            if rate:
                acc.arrival_price_in_sum = (Decimal(acc.arrival_price) * rate.rate).quantize(Decimal("0.01"))
                acc.sale_price_in_sum = (Decimal(acc.sale_price) * rate.rate).quantize(Decimal("0.01"))
            
            # Agar price_type SUM bo'lsa uni ham DOLLAR ga o'zgartirib qo'yamiz (chunki endi faqat DOLLAR)
            acc.price_type = Acceptance.PriceType.DOLLAR
            
            acc.save(update_fields=['arrival_price_in_dollar', 'sale_price_in_dollar', 'arrival_price_in_sum', 'sale_price_in_sum', 'price_type'])
            
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
                # Productdagi arrival_price va sale_price endi DOLLAR ni bildiradi
                product.arrival_price = last_acceptance.arrival_price_in_dollar
                product.sale_price = last_acceptance.sale_price_in_dollar

                # Productdagi so'm narxlarni ham Acceptance'dagi so'm narxlar bilan yangilaymiz
                product.arrival_price_in_sum = last_acceptance.arrival_price_in_sum
                product.sale_price_in_sum = last_acceptance.sale_price_in_sum
                
                product.save(update_fields=['arrival_price', 'sale_price', 'arrival_price_in_sum', 'sale_price_in_sum'])
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Bajarildi! Jami {updated_count} ta mahsulot narxi tiklandi."))