from django.contrib import admin
from supplier.models import Supplier, SupplierTransaction


class SupplierAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name", "phone_number"]


class SupplierTransactionAdmin(admin.ModelAdmin):
    list_display = ["id", "amount"]


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierTransaction, SupplierTransactionAdmin)
