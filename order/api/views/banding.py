from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from order.api.serializers import BandingGetSerializer, BandingPostSerializer
from order.models import Banding
from order.service.order import OrderService
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Banding"])
class BandingViewSet(BaseUserViewSet):
    queryset = Banding.objects.select_related("thickness").all()
    ordering = ["-created_at"]

    def get_queryset(self):
        date_param = self.request.query_params.get("date") or timezone.localdate()
        parsed_date = parse_date(date_param) if isinstance(date_param, str) else date_param
        if not parsed_date:
            return self.queryset.filter(created_at__date=date_param)

        start = timezone.make_aware(timezone.datetime.combine(parsed_date, timezone.datetime.min.time()))
        end = start + timezone.timedelta(days=1)
        return self.queryset.filter(created_at__gte=start, created_at__lt=end)

    def get_serializer_class(self):
        if self.action == "create":
            return BandingPostSerializer
        return BandingGetSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            banding = OrderService.create_banding(serializer.validated_data)
        except ValueError as e:
            raise ValidationError({"detail": str(e)})

        response = BandingGetSerializer(banding, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)
