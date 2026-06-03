import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from product.models import Product
from acceptance.models import Acceptance
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService
from user.models import User


class Command(BaseCommand):
    help = 'Imports acceptances from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_path', type=str, help='Path to the Excel file')
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID of the user who is making the import (defaults to the first superuser)',
            required=False
        )

    def handle(self, *args, **kwargs):
        excel_path = kwargs['excel_path']
        user_id = kwargs.get('user_id')

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

        self.stdout.write(f"Starting import using user: {user.full_name if hasattr(user, 'full_name') else user.username} ({user.id})")

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
            product_name_raw = row[0]
            
            product_name = str(product_name_raw).strip() if pd.notna(product_name_raw) else ""
            count_val = None
            for col_idx in range(1, len(df.columns)):
                if pd.notna(row[col_idx]):
                    try:
                        float(row[col_idx])
                        count_val = row[col_idx]
                        break
                    except ValueError:
                        pass
            
            if not product_name or count_val is None:
                 original_count = row[1] if len(df.columns) > 1 else 'N/A'
                 self.stdout.write(self.style.NOTICE(f"Row {index + 1}: Skipped because count is empty. (Name: '{product_name}', Count Col 1: '{original_count}')"))
                 skipped_count += 1
                 continue

            try:
                count = Decimal(str(count_val))
            except Exception:
                self.stdout.write(self.style.WARNING(f"Row {index + 1}: Invalid count format for product '{product_name}'. Count found: {count_val}"))
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

            data = {
                "product_id": product.id,
                "count": count,
                "price_type": Acceptance.PriceType.SUM,
                "arrival_price": 0,
                "sale_price": 0,
                "arrival_date": timezone.localdate(),
                "acceptance_status": Acceptance.AcceptanceStatus.WAITING,
                "description": "Imported from Excel via management command"
            }

            try:
                AcceptanceWorkflowService.create(data=data, user=user)
                self.stdout.write(self.style.SUCCESS(f"Row {index + 1}: Added '{product_name}' ({count})"))
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Failed to create acceptance for '{product_name}'. Error: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f"\\nImport finished! Successful: {success_count}, Errors: {error_count}, Skipped: {skipped_count}"))