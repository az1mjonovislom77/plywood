from drf_spectacular.utils import extend_schema
from utils.base.views_base import BaseUserViewSet
from utils.models import Currency
from utils.serializers import CurrencySerializer


@extend_schema(tags=["Currency"])
class CurrencyViewSet(BaseUserViewSet):
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
