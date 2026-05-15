import pandas as pd
from django.core.management.base import BaseCommand
from customer.models import Customer


class Command(BaseCommand):
    help = 'Imports customers from an Excel file (First column: Full Name)'

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

        success_count = 0
        error_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            customer_name_raw = row[0]
            
            customer_name = str(customer_name_raw).strip() if pd.notna(customer_name_raw) else ""

            if not customer_name:
                self.stdout.write(self.style.NOTICE(f"Row {index + 1}: Skipped because customer name is empty."))
                skipped_count += 1
                continue
                
            try:
                # Bazada shu ismli mijoz bor-yo'qligini tekshiramiz (Dublikat bo'lmasligi uchun)
                customer, created = Customer.objects.get_or_create(
                    full_name=customer_name,
                    defaults={
                        "description": "Excel orqali import qilingan"
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Row {index + 1}: Created customer '{customer_name}'"))
                    success_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"Row {index + 1}: Customer '{customer_name}' already exists. Skipped."))
                    skipped_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Failed to create customer '{customer_name}'. Error: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f"\\nImport finished! Successfully Created: {success_count}, Errors: {error_count}, Skipped (or Already Existed): {skipped_count}"))
