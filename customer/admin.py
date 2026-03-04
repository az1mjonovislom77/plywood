from customer.models import Customer, BalanceHistory
from django.contrib import admin


class CustomerAdmin(admin.ModelAdmin):
    pass


class BalanceHistoryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
admin.site.register(BalanceHistory, BalanceHistoryAdmin)