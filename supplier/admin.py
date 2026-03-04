from django.contrib import admin

from supplier.models import Supplier, SupplierTransaction


class SupplierAdmin(admin.ModelAdmin):
    pass


class SupplierTransactionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Supplier, SupplierAdmin)
admin.site.register(SupplierTransaction, SupplierTransactionAdmin)
