import math
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.db.models import Q
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from product.api.serializers import ProductSerializer
from product.models import Product
from product.services.product_export import MaterialReportService


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


def latin_to_cyrillic(text):
    mapping = {
        "sh": "ш", "ch": "ч", "ya": "я", "yo": "ё", "yu": "ю",
        "o‘": "ў", "g‘": "ғ",

        "a": "а", "b": "б", "d": "д", "e": "е", "f": "ф",
        "g": "г", "h": "х", "i": "и", "j": "ж", "k": "к",
        "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
        "q": "қ", "r": "р", "s": "с", "t": "т", "u": "у",
        "v": "в", "x": "х", "y": "й", "z": "з",
    }

    text = text.lower()

    for k in ["sh", "ch", "ya", "yo", "yu", "o‘", "g‘"]:
        text = text.replace(k, mapping[k])

    return "".join(mapping.get(c, c) for c in text)


def cyrillic_to_latin(text):
    mapping = {
        "ш": "sh", "ч": "ch", "я": "ya", "ё": "yo", "ю": "yu",
        "ў": "o‘", "ғ": "g‘",

        "а": "a", "б": "b", "д": "d", "е": "e", "ф": "f",
        "г": "g", "х": "h", "и": "i", "ж": "j", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
        "қ": "q", "р": "r", "с": "s", "т": "t", "у": "u",
        "в": "v", "й": "y", "з": "z",
    }

    return "".join(mapping.get(c, c) for c in text.lower())


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
            search_latin = cyrillic_to_latin(search)
            search_cyrillic = latin_to_cyrillic(search)
            vector = SearchVector("name", weight="A")
            query = SearchQuery(search)

            queryset = (
                queryset.annotate(rank=SearchRank(vector, query))
                .filter(Q(rank__gte=0.1) | Q(name__icontains=search)
                        | Q(name__icontains=search_latin) | Q(name__icontains=search_cyrillic))
                .order_by("-rank")
            )

        return queryset


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
