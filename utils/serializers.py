from utils.base.serializers_base import BaseReadSerializer
from utils.models import Currency


class CurrencySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Currency
