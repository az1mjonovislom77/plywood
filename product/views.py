from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from product.models import Product, Quality
from rest_framework import filters
from product.serializers import ProductSerializer, QualitySerializer
from utils.base.views_base import BaseUserViewSet
from django_filters.rest_framework import DjangoFilterBackend


@extend_schema(tags=["Product"])
class ProductViewSet(BaseUserViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category", "quality"]
    search_fields = ["name"]
    ordering = ["-id"]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


@extend_schema(tags=["Quality"])
class QualityViewSet(BaseUserViewSet):
    queryset = Quality.objects.all()
    serializer_class = QualitySerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    ordering = ["-id"]
