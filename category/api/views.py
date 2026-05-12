from drf_spectacular.utils import extend_schema
from category.models import Category
from category.api.serializers import CategorySerializer
from utils.base.views_base import BaseUserViewSet
from django.db.models import Count, Q
from utils.search import TransliteratedSearchFilter


@extend_schema(tags=["Category"])
class CategoryViewSet(BaseUserViewSet):
    queryset = Category.objects.annotate(product_count=Count('products', filter=Q(products__is_active=True)))
    serializer_class = CategorySerializer
    ordering = ['-id']

    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['name']
