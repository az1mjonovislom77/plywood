from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin
from utils.models import Currency, NotificationSettings, Expenses, ExpensesHistory, ServicesName, Services


@admin.register(Currency)
class CurrencyAdmin(NameOnlyAdmin):
    pass


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ["low_stock_threshold"]


@admin.register(Expenses)
class ExpensesAdmin(admin.ModelAdmin):
    list_display = ["expense_status", "description"]


@admin.register(ExpensesHistory)
class ExpensesHistoryAdmin(admin.ModelAdmin):
    list_display = ["action", "description"]


@admin.register(ServicesName)
class ServicesNameAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]


@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ["id", "description"]
