from drf_spectacular.utils import extend_schema
from product.models import Product
from rest_framework import filters
from product.serializers import ProductSerializer
from utils.base.views_base import BaseUserViewSet
from django_filters.rest_framework import DjangoFilterBackend


@extend_schema(tags=["Product"])
class ProductViewSet(BaseUserViewSet):
    serializer_class = ProductSerializer
    ordering = ['-id']

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'quality']
    search_fields = ['name']

    def get_queryset(self):
        return Product.objects.select_related('category')
