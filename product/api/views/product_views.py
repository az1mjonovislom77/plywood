import math
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from product.api.serializers import ProductSerializer
from product.models import Product


class ProductPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "limit"

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


@extend_schema(
    tags=["Product"],
    parameters=[OpenApiParameter(name="search", description="Product search", required=False, type=OpenApiTypes.STR)],
)
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=True)
    serializer_class = ProductSerializer
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category", "quality"]
    ordering = ["-id"]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")

        if search:
            vector = SearchVector("name", weight="A")
            query = SearchQuery(search)
            queryset = (
                queryset.annotate(rank=SearchRank(vector, query))
                .filter(Q(rank__gte=0.1) | Q(name__icontains=search))
                .order_by("-rank")
            )

        return queryset
