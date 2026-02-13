from acceptance.models import Acceptance, AcceptanceHistory
from django.contrib import admin


class AcceptanceAdmin(admin.ModelAdmin):
    list_display = ("id",)


class AcceptanceHistoryAdmin(admin.ModelAdmin):
    list_display = ("id",)


admin.site.register(Acceptance, AcceptanceAdmin)
admin.site.register(AcceptanceHistory, AcceptanceHistoryAdmin)
