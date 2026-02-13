from acceptance.models import Acceptance, AcceptanceHistory
from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin


class AcceptanceAdmin(NameOnlyAdmin):
    pass


admin.site.register(Acceptance, AcceptanceAdmin)


class AcceptanceHistoryAdmin(NameOnlyAdmin):
    pass


admin.site.register(AcceptanceHistory, AcceptanceHistoryAdmin)
