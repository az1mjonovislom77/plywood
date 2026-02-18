from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.base.views_base import BaseUserViewSet
from utils.models import Currency
from utils.serializers import CurrencySerializer
from utils.service.dasboard_stats import DashboardStatsService
from utils.service.notification_service import ProductNotificationService


@extend_schema(tags=["Currency"])
class CurrencyViewSet(BaseUserViewSet):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()


@extend_schema(tags=["Notifications"])
class LowStockNotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = ProductNotificationService.get_low_stock_info()
        return Response(data)


@extend_schema(tags=["Dashboard"])
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = DashboardStatsService.get_stats()
        return Response(data)
