from order.models import Basket, Cutting
from django.contrib import admin


class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_active")


class CuttingAdmin(admin.ModelAdmin):
    list_display = ("id", "count")


admin.site.register(Basket, BasketAdmin)
admin.site.register(Cutting, CuttingAdmin)
