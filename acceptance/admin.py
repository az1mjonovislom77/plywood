from acceptance.models import Acceptance, AcceptanceHistory, CurrencyRate
from django.contrib import admin


class AcceptanceAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "product", "count")
    list_select_related = ("supplier", "product")


class AcceptanceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id",)
    list_select_related = ("product",)


class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ("id", "rate", "date")


admin.site.register(Acceptance, AcceptanceAdmin)
admin.site.register(AcceptanceHistory, AcceptanceHistoryAdmin)
admin.site.register(CurrencyRate, CurrencyRateAdmin)
