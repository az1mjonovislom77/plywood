import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from customer.models import Customer
from customer.service.statement_service import CustomerStatementService

c = Customer.objects.first()
if c:
    try:
        content = CustomerStatementService.build_statement_excel(c.id)
        print("Success, length:", len(content.getvalue()))
    except Exception as e:
        print("Exception:", e)
else:
    print("No customer")
