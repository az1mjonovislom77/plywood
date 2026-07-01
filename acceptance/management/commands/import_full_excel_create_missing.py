import sys
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from product.models import Product
from acceptance.models import Acceptance
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService
from user.models import User


def _make_utf8_safe(stream):
    if hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    return stream


class Command(BaseCommand):
    help = (
        'Imports acceptances from an Excel file with 4 columns: Name, Count, Arrival Price, Sale Price. '
        'Unlike import_full_excel, any product name not found in the database is created automatically '
        '(with no category assigned) before the acceptance is recorded.'
    )

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file')
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user who is making the import (defaults to the first superuser)',
            required=False
        )
        parser.add_argument(
            '--start-row',
            type=int,
            default=1,
            help='1-based row number to start processing from (use to resume an interrupted import)',
            required=False
        )

    def handle(self, *args, **kwargs):
        _make_utf8_safe(sys.stdout)
        _make_utf8_safe(sys.stderr)

        excel_path = kwargs['excel_path']
        user_id = kwargs.get('user_id')
        start_row = kwargs.get('start_row') or 1

        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found."))
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()

            if not user:
                self.stdout.write(self.style.ERROR("No users found in the database. Please specify a user ID."))
                return

        self.stdout.write(
            f"Starting import using user: {user.full_name if hasattr(user, 'full_name') else user.username} ({user.id})")

        try:
            df = pd.read_excel(excel_path, header=None)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read Excel file: {str(e)}"))
            return

        if df.empty:
            self.stdout.write(self.style.WARNING("The Excel file is empty or could not be read properly."))
            return

        self.stdout.write(f"Found {len(df)} rows in the Excel file.")

        if len(df.columns) < 4:
            self.stdout.write(self.style.ERROR(
                "Excel file must have at least four columns: Product Name, Count, Arrival Price, Sale Price"))
            return

        success_count = 0
        created_product_count = 0
        error_count = 0
        skipped_count = 0

        for index, row in df.iterrows():
            if index + 1 < start_row:
                continue

            product_name_raw = row[0]
            count_val = row[1]
            arrival_price_val = row[2]
            sale_price_val = row[3]
            product_name = str(product_name_raw).strip() if pd.notna(product_name_raw) else ""

            if not product_name or pd.isna(count_val) or pd.isna(arrival_price_val) or pd.isna(sale_price_val):
                self.stdout.write(self.style.NOTICE(f"Row {index + 1}: Skipped because one of the fields is empty."))
                skipped_count += 1
                continue

            try:
                count = Decimal(str(count_val))
                arrival_price = Decimal(str(arrival_price_val))
                sale_price = Decimal(str(sale_price_val))
            except Exception:
                self.stdout.write(
                    self.style.WARNING(f"Row {index + 1}: Invalid number format for product '{product_name}'"))
                error_count += 1
                continue

            try:
                product = Product.objects.get(name__iexact=product_name)
            except Product.DoesNotExist:
                product = Product.objects.create(name=product_name)
                created_product_count += 1
                self.stdout.write(self.style.SUCCESS(f"Row {index + 1}: Created new product '{product_name}'"))
            except Product.MultipleObjectsReturned:
                self.stdout.write(
                    self.style.ERROR(f"Row {index + 1}: Multiple products found with name '{product_name}'"))
                error_count += 1
                continue

            data = {
                "product_id": product.id,
                "count": count,
                "price_type": Acceptance.PriceType.DOLLAR,  # Valyuta Dollar qilib belgilandi
                "arrival_price": arrival_price,
                "sale_price": sale_price,
                "arrival_date": timezone.localdate(),
                "acceptance_status": Acceptance.AcceptanceStatus.WAITING,
                "description": "Imported from Excel with count and prices"
            }

            try:
                AcceptanceWorkflowService.create(data=data, user=user)
                self.stdout.write(self.style.SUCCESS(
                    f"Row {index + 1}: Added '{product_name}' (Count: {count}, Arrival: ${arrival_price}, Sale: ${sale_price})"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Row {index + 1}: Failed to create acceptance for '{product_name}'. Error: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nImport finished! Successful: {success_count}, New products created: {created_product_count}, "
            f"Errors: {error_count}, Skipped: {skipped_count}"))
