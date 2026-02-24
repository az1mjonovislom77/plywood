from product.models import Product, Quality
from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin


class ProductAdmin(NameOnlyAdmin):
    pass


class QualityAdmin(NameOnlyAdmin):
    pass


admin.site.register(Product, ProductAdmin)
admin.site.register(Quality, QualityAdmin)
