from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from order.service.dashboard_stats import OrderStatsService

@extend_schema(tags=['OrderStats'])
class OrderStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = OrderStatsService.get_stats()
        return Response(data)
