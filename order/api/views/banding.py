from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from order.api.serializers import BandingGetSerializer, BandingPostSerializer, BandingStatsSerializer
from order.models import Banding
from order.service.cutting_banding_stats import PriceBreakdownService
from order.service.order import OrderService
from utils.base.views_base import BaseUserViewSet


@extend_schema(
    tags=["Banding"],
    parameters=[
        OpenApiParameter(name="from", required=False, type=OpenApiTypes.STR),
        OpenApiParameter(name="to", required=False, type=OpenApiTypes.STR)])
class BandingViewSet(BaseUserViewSet):
    queryset = Banding.objects.select_related("customer").all()
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = self.queryset
        from_date = self.request.query_params.get("from")
        to_date = self.request.query_params.get("to")

        if from_date:
            parsed_from = parse_date(from_date)
            if parsed_from:
                start = timezone.make_aware(timezone.datetime.combine(parsed_from, timezone.datetime.min.time()))
                queryset = queryset.filter(created_at__gte=start)
        
        if to_date:
            parsed_to = parse_date(to_date)
            if parsed_to:
                end = timezone.make_aware(timezone.datetime.combine(parsed_to, timezone.datetime.min.time())) + timezone.timedelta(days=1)
                queryset = queryset.filter(created_at__lt=end)
        
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return BandingPostSerializer
        return BandingGetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        bandings = list(queryset)
        by_price = PriceBreakdownService.banding_by_price(queryset)

        stats = BandingStatsSerializer({
            "bandings_count": len(bandings),
            "total_length": sum((row["total_length"] for row in by_price), Decimal("0")),
            "by_price": by_price})

        return Response({
            "stats": stats.data,
            "data": self.get_serializer(bandings, many=True).data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            banding = OrderService.create_banding(serializer.validated_data)
        except ValueError as e:
            raise ValidationError({"detail": str(e)})

        response = BandingGetSerializer(banding, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)
