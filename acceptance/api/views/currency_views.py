from datetime import date
from decimal import Decimal
import requests
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from acceptance.models import CurrencyRate


@extend_schema(tags=["UpdateCurrency"])
class UpdateCurrencyRateView(APIView):
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
