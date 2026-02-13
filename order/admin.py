from order.models import Basket
from django.contrib import admin


class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", 'product')


admin.site.register(Basket, BasketAdmin)
