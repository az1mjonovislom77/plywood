from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from customer.service.customer_stats import CustomerStatsService
from rest_framework.response import Response
from customer.service.debt_stats import DashboardStatsService


@extend_schema(tags=["CustomerStats"])
class CustomerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = CustomerStatsService.dashboard()

        return Response(stats, status=status.HTTP_200_OK)


@extend_schema(tags=["CustomerStats"])
class DashboardDebtStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = DashboardStatsService.get_debt_stats()
        return Response(data)
