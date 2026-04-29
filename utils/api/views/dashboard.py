from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from utils.service.all_stats import ALlDashboardStatsService
from utils.service.comprehensive_stats import DashboardStatsService as ComprehensiveStatsService
from utils.service.daily_stats import DailyDashboardStatsService
from utils.service.dasboard_stats import DashboardStatsService
from rest_framework import status
from utils.service.range_stats import DashboardRangeStatsService


@extend_schema(tags=["Dashboard"], parameters=[
    OpenApiParameter(name="date", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False)])
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.query_params.get("date")
        try:
            data = DashboardStatsService.get_stats(date_str=date_str)
            return Response(data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        try:
            data = DailyDashboardStatsService.get_daily_stats(date_str)
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Dashboard"])
class CashboxTotalStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            data = ALlDashboardStatsService.get_all_stats()
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Dashboard"],
    parameters=[
        OpenApiParameter(name="from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
        OpenApiParameter(name="to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=False),
    ],
)
class ComprehensiveDashboardStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        try:
            data = ComprehensiveStatsService.get_stats(date_from, date_to)
            return Response(data, status=status.HTTP_200_OK)

        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
