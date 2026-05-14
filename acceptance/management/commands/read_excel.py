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

        if len(df.columns) < 2:
            self.stdout.write(self.style.ERROR("Excel file must have at least two columns: Product Name and Count"))
            return

        success_count = 0
        error_count = 0

        for index, row in df.iterrows():
            product_name = str(row[0]).strip()
            count_val = row[1]
            
            if pd.isna(product_name) or not product_name or pd.isna(count_val):
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
                self.stdout.write(self.style.ERROR(f"Row {index + 1}: Product '{product_name}' not found"))
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

        self.stdout.write(self.style.SUCCESS(f"\\nImport finished! Successful: {success_count}, Errors: {error_count}"))
