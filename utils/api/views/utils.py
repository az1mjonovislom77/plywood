from math import ceil
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.base.views_base import BaseUserViewSet
from utils.models import Currency, Services, ServicesName
from utils.api.serializers import CurrencySerializer, ServicesSerializer, ServicesNameSerializer
from utils.service.notification_service import ProductNotificationService


@extend_schema(tags=["Currency"])
class CurrencyViewSet(BaseUserViewSet):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()


class LowStockNotificationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)

        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": ceil(total / limit) if limit else 0,
            "low_stock_products": total,
            "products": data,
        })


@extend_schema(
    tags=["Notifications"],
    parameters=[
        OpenApiParameter(name="page", required=False, type=int),
        OpenApiParameter(name="limit", required=False, type=int),
    ],
)
class LowStockNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LowStockNotificationPagination

    def get(self, request):
        queryset = ProductNotificationService.get_low_stock_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            return paginator.get_paginated_response(page)

        return Response({
            "low_stock_products": queryset.count(),
            "products": list(queryset),
        })


@extend_schema(tags=["ServicesName"])
class ServicesNameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = ServicesName.objects.all()
        serializer = ServicesNameSerializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Services"])
class ServicesViewSet(BaseUserViewSet):
    queryset = Services.objects.select_related("services_name")
    serializer_class = ServicesSerializer
