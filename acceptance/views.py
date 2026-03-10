import requests
from decimal import Decimal
from datetime import date
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema
from acceptance.models import CurrencyRate
from utils.base.views_base import BaseUserViewSet
from .models import Acceptance, AcceptanceHistory
from .serializers import AcceptanceSerializer, AcceptanceHistorySerializer, AcceptanceCancelSerializer
from .service.acceptance_workflow import AcceptanceWorkflowService


@extend_schema(tags=["Acceptance"])
class AcceptanceViewSet(BaseUserViewSet):
    queryset = Acceptance.objects.select_related("product", "supplier", "accepted_by").prefetch_related("histories")
    serializer_class = AcceptanceSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        acceptance = AcceptanceWorkflowService.create(data=serializer.validated_data, user=self.request.user)
        serializer.instance = acceptance

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        acceptance = AcceptanceWorkflowService.accept(acceptance_id=pk, user=request.user)
        serializer = self.get_serializer(acceptance)

        return Response(serializer.data)

    @extend_schema(request=AcceptanceCancelSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        description = request.data.get("description")
        acceptance = AcceptanceWorkflowService.cancel(pk, request.user, description)
        serializer = self.get_serializer(acceptance)

        return Response(serializer.data)


@extend_schema(tags=["AcceptanceHistory"])
class AcceptanceHistoryViewSet(ModelViewSet):
    queryset = AcceptanceHistory.objects.select_related("product", "acceptance")
    serializer_class = AcceptanceHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]
    pagination_class = None


@extend_schema(tags=["UpdateCurrency"])
class UpdateCurrencyRateView(APIView):
    permission_classes = [IsAuthenticated]
    CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/"

    def get(self, request):
        today = date.today()
        rate_obj, created = CurrencyRate.objects.get_or_create(date=today, defaults={"rate": self._fetch_rate()})
        status = "created" if created else "already_exists"

        return Response({
            "date": rate_obj.date,
            "rate": rate_obj.rate,
            "status": status,
        })

    def _fetch_rate(self) -> Decimal:
        try:
            response = requests.get(self.CBU_URL, timeout=10)
            response.raise_for_status()
            data = response.json()[0]

            return Decimal(data["Rate"])

        except (requests.RequestException, KeyError, IndexError) as exc:
            raise RuntimeError(f"Currency API error: {exc}")
