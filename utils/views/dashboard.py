from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.service.all_stats import ALlDashboardStatsService
from utils.service.daily_stats import DailyDashboardStatsService
from utils.service.dasboard_stats import DashboardStatsService
from rest_framework import status
from utils.service.range_stats import DashboardRangeStatsService


@extend_schema(tags=["Dashboard"])
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = DashboardStatsService.get_stats()
        return Response(data)


@extend_schema(
    tags=["Dashboard"],
    parameters=[
        OpenApiParameter(name="from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
        OpenApiParameter(name="to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False)])
class DashboardRangeStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        try:
            data = DashboardRangeStatsService.get_range_stats(date_from, date_to)
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Dashboard"],
               parameters=[OpenApiParameter(name="date", type=OpenApiTypes.DATE,
                                            location=OpenApiParameter.QUERY, required=False)])
class DashboardDailyStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get("date")

        if date_str:
            try:
                data = DailyDashboardStatsService.get_daily_stats(date_str)
                return Response(data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                data = ALlDashboardStatsService.get_all_stats()
                return Response(data, status=status.HTTP_200_OK)
            except ValueError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
