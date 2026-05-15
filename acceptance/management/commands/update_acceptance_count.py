import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from product.models import Product
from acceptance.models import Acceptance, AcceptanceHistory


class Command(BaseCommand):
    help = 'Updates the count of existing WAITING acceptances from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file')

    def handle(self, *args, **kwargs):
        excel_path = kwargs['excel_path']

        try:
            df = pd.read_excel(excel_path, header=None)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read Excel file: {str(e)}"))
            return

        if df.empty:
            self.stdout.write(self.style.WARNING("The Excel file is empty or could not be read properly."))
            return
            
        self.stdout.write(f"Found {len(df)} rows in the Excel file.")

        if len(df.columns) < 2:
            self.stdout.write(self.style.ERROR("Excel file must have at least two columns: Product Name and Count"))
            return

        success_count = 0
        error_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            product_name_raw = row[0]
            count_val = row[1]
            
            product_name = str(product_name_raw).strip() if pd.notna(product_name_raw) else ""

            if not product_name or pd.isna(count_val):
                self.stdout.write(self.style.NOTICE(f"Row {index + 1}: Skipped because product name or count is empty."))
                skipped_count += 1
                continue
                
            try:
                count = Decimal(str(count_val))
            except Exception:
                self.stdout.write(self.style.WARNING(f"Row {index + 1}: Invalid count format for product '{product_name}'"))
                error_count += 1
                continue

            try:
                product = Product.objects.get(name__iexact=product_name)
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Product '{product_name}' not found in database."))
                error_count += 1
                continue
            except Product.MultipleObjectsReturned:
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Multiple products found with name '{product_name}'"))
                error_count += 1
                continue

            # Kutish holatidagi qabulni qidirish
            acceptances = Acceptance.objects.filter(
                product=product, 
                acceptance_status=Acceptance.AcceptanceStatus.WAITING
            ).order_by('-created_at')
            
            if not acceptances.exists():
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: No 'WAITING' acceptance found for '{product_name}'"))
                error_count += 1
                continue
                
            # Agar bir xil mahsulotdan bir nechta kutish holatidagilari bo'lsa, eng oxirgisini oladi
            acceptance = acceptances.first()
            old_count = acceptance.count
            
            # Miqdorni yangilash
            acceptance.count = count
            acceptance.save(update_fields=['count'])
            
            # Historydagi yaratilgan vaqtidagi miqdorni ham to'g'rilab qo'yamiz (logika buzilmasligi uchun)
            history = AcceptanceHistory.objects.filter(
                acceptance=acceptance, 
                action=AcceptanceHistory.Action.CREATE
            ).first()
            if history:
                history.count = count
                history.save(update_fields=['count'])

            self.stdout.write(self.style.SUCCESS(f"Row {index + 1}: Updated '{product_name}' count from {old_count} to {count}"))
            success_count += 1

        self.stdout.write(self.style.SUCCESS(f"\\nUpdate finished! Successful: {success_count}, Errors: {error_count}, Skipped: {skipped_count}"))