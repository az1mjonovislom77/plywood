import math
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from product.models import Product, Quality
from rest_framework import filters, viewsets
from product.serializers import ProductSerializer, QualitySerializer
from utils.base.views_base import BaseUserViewSet
from django_filters.rest_framework import DjangoFilterBackend


class ProductPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = math.ceil(total / limit)

        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "data": data,
        })


@extend_schema(tags=["Product"])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = ProductPagination

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
