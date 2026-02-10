from category.models import Category
from utils.base.admin_base import NameOnlyAdmin
from django.contrib import admin


class CategoryAdmin(NameOnlyAdmin):
    pass


admin.site.register(Category, CategoryAdmin)
