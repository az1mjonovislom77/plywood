from product.models import Product
from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin


class ProductAdmin(NameOnlyAdmin):
    pass


admin.site.register(Product, ProductAdmin)
