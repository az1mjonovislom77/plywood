from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from order.api.serializers import CuttingCreateSerializer, CuttingSerializer
from order.models import Cutting
from order.service.order import OrderService
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Cutting"])
class CuttingViewSet(BaseUserViewSet):
    queryset = Cutting.objects.select_related("customer").all()
    serializer_class = CuttingSerializer
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return CuttingCreateSerializer
        return CuttingSerializer

    def get_queryset(self):
        date_param = self.request.query_params.get("date") or timezone.localdate()
        parsed_date = parse_date(date_param) if isinstance(date_param, str) else date_param
        if not parsed_date:
            return self.queryset.filter(created_at__date=date_param)

        start = timezone.make_aware(timezone.datetime.combine(parsed_date, timezone.datetime.min.time()))
        end = start + timezone.timedelta(days=1)
        return self.queryset.filter(created_at__gte=start, created_at__lt=end)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cutting = OrderService.create_cutting(serializer.validated_data)
        except ValueError as e:
            raise ValidationError({"detail": str(e)})

        response = CuttingSerializer(cutting, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)
