import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from user.models import User
from supplier.models import Supplier
from product.models import Product
from acceptance.models import Acceptance, CurrencyRate
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService

user = User.objects.first()
supplier = Supplier.objects.first()
if not supplier:
    supplier = Supplier.objects.create(full_name="Test Supplier", phone_number="123")

product = Product.objects.first()
if not product:
    product = Product.objects.create(name="Test Product")

rate = CurrencyRate.objects.first()
if not rate:
    rate = CurrencyRate.objects.create(date=timezone.localdate(), rate=Decimal("12000.00"))

print(f"Supplier starting debt: {supplier.debt}")

# Create an acceptance
data = {
    "supplier": supplier,
    "product": product,
    "arrival_price": Decimal("10.00"),
    "sale_price": Decimal("15.00"),
    "count": Decimal("100"),
    "arrival_date": timezone.localdate()
}
acceptance = AcceptanceWorkflowService.create(data, user)
print(f"Acceptance created. Status: {acceptance.acceptance_status}. Supplier debt: {Supplier.objects.get(id=supplier.id).debt}")

# Accept it
AcceptanceWorkflowService.accept(acceptance.id, user)
acceptance.refresh_from_db()
print(f"Acceptance accepted. Status: {acceptance.acceptance_status}. Supplier debt: {Supplier.objects.get(id=supplier.id).debt}")

# Update it
update_data = {
    "arrival_price": Decimal("20.00"),
}
AcceptanceWorkflowService.update(acceptance, update_data, user)
acceptance.refresh_from_db()
print(f"Acceptance updated. New arrival price: {acceptance.arrival_price}. Supplier debt: {Supplier.objects.get(id=supplier.id).debt}")
