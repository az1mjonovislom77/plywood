from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from utils.base.views_base import BaseUserViewSet
from .models import Acceptance, AcceptanceHistory
from .serializers import AcceptanceSerializer, AcceptanceHistorySerializer


@extend_schema(tags=["Acceptance"])
class AcceptanceViewSet(BaseUserViewSet):
    queryset = Acceptance.objects.select_related("product").all()
    serializer_class = AcceptanceSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        acceptance = serializer.save()
        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            product=acceptance.product,
            arrival_price=acceptance.arrival_price,
            sale_price=acceptance.sale_price,
            count=acceptance.count,
            arrival_date=acceptance.arrival_date,
            description=acceptance.description,
        )


@extend_schema(tags=["AcceptanceHistory"])
class AcceptanceHistoryViewSet(ModelViewSet):
    queryset = AcceptanceHistory.objects.select_related("product", "acceptance").all()
    serializer_class = AcceptanceHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]
