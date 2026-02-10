from drf_spectacular.utils import extend_schema
from category.models import Category
from rest_framework import filters
from category.serializers import CategorySerializer
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Category"])
class CategoryViewSet(BaseUserViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ['-id']

    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
