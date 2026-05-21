import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from decimal import Decimal
from django.utils import timezone
from user.models import User
from supplier.models import Supplier, SupplierTransaction
from product.models import Product
from acceptance.models import Acceptance, CurrencyRate
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService

user = User.objects.first()
supplier = Supplier.objects.create(full_name="Test Supplier 2", phone_number="123")
product = Product.objects.create(name="Test Product 2")
rate = CurrencyRate.objects.create(date=timezone.localdate(), rate=Decimal("10000.00"))

print(f"Initial Supplier debt: {supplier.debt}")

data = {
    "supplier": supplier,
    "product": product,
    "arrival_price": Decimal("10.00"),
    "sale_price": Decimal("15.00"),
    "count": Decimal("10"),
    "arrival_date": timezone.localdate()
}
acceptance = AcceptanceWorkflowService.create(data, user)
AcceptanceWorkflowService.accept(acceptance.id, user)
supplier.refresh_from_db()
print(f"Debt after accept: {supplier.debt}")

update_data = {
    "arrival_price": Decimal("20.00"),
}
AcceptanceWorkflowService.update(acceptance, update_data, user)
supplier.refresh_from_db()
print(f"Debt after update: {supplier.debt}")
