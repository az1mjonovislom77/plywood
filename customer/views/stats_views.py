from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from customer.service.customer_stats import CustomerStatsService
from rest_framework.response import Response


class CustomerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = CustomerStatsService.dashboard()

        return Response(stats, status=status.HTTP_200_OK)
