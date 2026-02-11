from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin

from utils.models import Currency


class CurrencyAdmin(NameOnlyAdmin):
    pass


admin.site.register(Currency, CurrencyAdmin)
