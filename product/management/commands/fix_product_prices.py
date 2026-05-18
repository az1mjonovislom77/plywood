from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance


class Command(BaseCommand):
    help = "Fixes the arrival_price_in_dollar, arrival_price, and sale_price for all products based on the last acceptance"

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
                needs_update = False
                
                # Sotish narxi valyutada (DOLLAR yoki SUM) bo'lishidan qat'iy nazar, 
                # oxirgi hisoblangan SUM dagi narxni productga yozamiz.
                # Yoki aslicha (sale_price / arrival_price) yozib qo'yamizmi?
                # Odatda Product modelida arrival_price va sale_price bor (ular so'm yoki dollar bo'lishi mumkin)
                # Acceptance da sale_price va sale_price_in_sum bor
                # Agar kelish narxi dollar bolsa, arrival_price_in_sum yozilishi kerakmidi?
                # Hozir shunday qilsak, barcha narxlarni sinxronlashtirib qo'yishimiz mumkin:
                
                # Dollar kelish narxini to'g'irlash
                if product.arrival_price_in_dollar != last_acceptance.arrival_price_in_dollar:
                    product.arrival_price_in_dollar = last_acceptance.arrival_price_in_dollar
                    needs_update = True
                
                # So'mdagi kelish narxini to'g'irlash
                if product.arrival_price != last_acceptance.arrival_price_in_sum:
                    product.arrival_price = last_acceptance.arrival_price_in_sum
                    needs_update = True

                # So'mdagi sotish narxini to'g'irlash
                if product.sale_price != last_acceptance.sale_price_in_sum:
                    product.sale_price = last_acceptance.sale_price_in_sum
                    needs_update = True

                if needs_update:
                    product.save(update_fields=['arrival_price_in_dollar', 'arrival_price', 'sale_price'])
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"Updated prices for '{product.name}' (ID: {product.id}). "
                        f"Arrival $: {product.arrival_price_in_dollar}, "
                        f"Arrival UZS: {product.arrival_price}, "
                        f"Sale UZS: {product.sale_price}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"Finished fixing prices. Total products updated: {updated_count}"
        ))