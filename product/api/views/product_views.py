import math
from decimal import Decimal
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from product.api.serializers import ProductSerializer
from product.models import Product
from product.services.export_json import MaterialReportJsonService
from product.services.product_export import MaterialReportService
from product.services.product_excel_export import ProductExcelExportService
from utils.search import build_transliterated_search_q
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField


class ProductPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = math.ceil(total / limit)
        all_investment_in_dollar = Decimal('0')

        if hasattr(self.page.paginator, "object_list"):
            queryset = self.page.paginator.object_list
            total_investment = queryset.aggregate(
                total=Sum(ExpressionWrapper(F('count') * F('arrival_price'), output_field=DecimalField()))
            )['total'] or Decimal('0')
            all_investment_in_dollar = float(total_investment)

        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "all_investment_in_dollar": all_investment_in_dollar,
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
                .filter(build_transliterated_search_q(["name"], search) | Q(rank__gte=0.1))
                .order_by("-rank")
            )

        return queryset

    @extend_schema(
        tags=["ProductExport"],
        parameters=[
            OpenApiParameter(name="search", description="Product search", required=False, type=OpenApiTypes.STR),
            OpenApiParameter(name="category", description="Filter by category id", required=False,
                             type=OpenApiTypes.INT),
            OpenApiParameter(name="quality", description="Filter by quality", required=False, type=OpenApiTypes.STR)
        ]
    )
    @action(detail=False, methods=["get"], url_path="export_all")
    def export_excel(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        file = ProductExcelExportService.build_excel(queryset, user=request.user)

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="products_export.xlsx"'},
        )


@extend_schema(
    tags=["ProductExport"],
    parameters=[
        OpenApiParameter(name="from", required=False, type=str),
        OpenApiParameter(name="to", required=False, type=str)]
)
class MaterialReportExcelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        file = MaterialReportService.build_excel(date_from=date_from, date_to=date_to)

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="material_report.xlsx"'},
        )


@extend_schema(
    tags=["ProductReport"],
    parameters=[
        OpenApiParameter(name="from", required=False, type=str),
        OpenApiParameter(name="to", required=False, type=str),
    ],
)
class MaterialReportJsonViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(MaterialReportJsonService.build(
            date_from=request.query_params.get("from"),
            date_to=request.query_params.get("to")))


@extend_schema(
    tags=["Product"],
    parameters=[OpenApiParameter(name="search", description="Product search", required=False, type=OpenApiTypes.STR)],
)
class DeletedProductsViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").filter(is_active=False)
    serializer_class = ProductSerializer
    http_method_names = ["get", "post"]
    permission_classes = [IsAuthenticated]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category", "quality"]
    ordering = ["-id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search")

        if search:
            vector = SearchVector("name", weight="A")
            query = SearchQuery(search)

            queryset = (
                queryset.annotate(rank=SearchRank(vector, query))
                .filter(build_transliterated_search_q(["name"], search) | Q(rank__gte=0.1))
                .order_by("-rank")
            )

        return queryset

    @extend_schema(tags=["Product"])
    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, pk=None):
        instance = self.get_object()
        instance.is_active = True
        instance.save(update_fields=["is_active"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)