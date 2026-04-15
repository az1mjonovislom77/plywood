from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from supplier.service.stats import SupplierStatsService


@extend_schema(tags=["SupplierStats"])
class SupplierDebtStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = SupplierStatsService.get_debt_stats()
        return Response(stats)
