from drf_spectacular.utils import extend_schema
from product.models import Product
from rest_framework import filters
from product.serializers import ProductSerializer, ManagerProductSerializer
from utils.base.views_base import BaseUserViewSet, User
from django_filters.rest_framework import DjangoFilterBackend


@extend_schema(tags=["Product"])
class ProductViewSet(BaseUserViewSet):
    ordering = ['-id']

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'quality']
    search_fields = ['name']

    def get_queryset(self):
        return Product.objects.select_related('category')

    def get_serializer_class(self):
        user = self.request.user
        if user.role == User.UserRoles.MANAGER:
            return ManagerProductSerializer
        return ProductSerializer
