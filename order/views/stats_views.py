from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from order.service.cutting_banding_stats import DashboardStatsService
from order.service.dashboard_stats import OrderStatsService
from order.service.last7day_stats import Last7dayStatsService


@extend_schema(tags=['OrderStats'])
class OrderStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = OrderStatsService.get_stats()
        return Response(data)


@extend_schema(tags=["CuttingBandingStats"])
class CuttingBandingIncomeStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = DashboardStatsService.get_cutting_banding_income()
        return Response(data)


@extend_schema(tags=["Dashboard"])
class Last7DaysIncomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = Last7dayStatsService.get_last_7_days_income()
        return Response(data)
