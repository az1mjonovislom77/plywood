from customer.models import Customer, BalanceHistory
from django.contrib import admin


class CustomerAdmin(admin.ModelAdmin):
    list_display = ["id", "full_name"]


class BalanceHistoryAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
admin.site.register(BalanceHistory, BalanceHistoryAdmin)
