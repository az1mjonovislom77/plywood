from customer.models import Customer
from django.contrib import admin


class CustomerAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
