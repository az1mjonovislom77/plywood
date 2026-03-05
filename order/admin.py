from order.models import Basket, Cutting, Thickness, Banding, Order, OrderHistory
from django.contrib import admin


class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "is_active")


class CuttingAdmin(admin.ModelAdmin):
    list_display = ("id", "count")


class ThicknessAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "price")


class BandingAdmin(admin.ModelAdmin):
    list_display = ("id", "length")


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "payment_method")


class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order")


admin.site.register(Banding, BandingAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderHistory, OrderHistoryAdmin)
admin.site.register(Thickness, ThicknessAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Cutting, CuttingAdmin)
