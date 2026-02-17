from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin

from utils.models import Currency, NotificationSettings


@admin.register(Currency)
class CurrencyAdmin(NameOnlyAdmin):
    pass


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ["low_stock_threshold"]
