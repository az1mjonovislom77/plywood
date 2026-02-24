import requests
from decimal import Decimal
from datetime import date
from rest_framework.views import APIView
from rest_framework.response import Response
from acceptance.models import CurrencyRate
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from utils.base.views_base import BaseUserViewSet
from .models import Acceptance, AcceptanceHistory
from .serializers import AcceptanceSerializer, AcceptanceHistorySerializer, CurrencyRateSerializer


@extend_schema(tags=["Acceptance"])
class AcceptanceViewSet(BaseUserViewSet):
    queryset = Acceptance.objects.select_related("product").all()
    serializer_class = AcceptanceSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=["AcceptanceHistory"])
class AcceptanceHistoryViewSet(ModelViewSet):
    queryset = AcceptanceHistory.objects.select_related("product", "acceptance").all()
    serializer_class = AcceptanceHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]
    pagination_class = None


@extend_schema(tags=["UpdateCurrency"])
class UpdateCurrencyRateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = date.today()

        existing = CurrencyRate.objects.filter(date=today).first()
        if existing:
            return Response({"date": existing.date, "rate": existing.rate, "status": "already_exists"})

        try:
            response = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/", timeout=10)
            data = response.json()[0]
            rate = Decimal(data["Rate"])
            obj = CurrencyRate.objects.create(date=today, rate=rate)

            return Response({
                "date": obj.date,
                "rate": obj.rate,
                "status": "created"
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
