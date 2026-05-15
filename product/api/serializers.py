from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from django.utils import timezone
from acceptance.models import CurrencyRate
from product.models import Product, Quality
from utils.base.serializers_base import TrimmedDecimalField


class ProductSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=10, decimal_places=3, read_only=True)
    sale_price_in_dollar = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["arrival_price", "arrival_price_in_dollar", "sale_price", "count", "is_active"]

    def _get_rate(self):
        if not hasattr(self, "_rate_cache"):
            rate_obj = CurrencyRate.objects.filter(date__lte=timezone.localdate()).order_by("-date").first()
            self._rate_cache = rate_obj.rate if rate_obj else None
        return self._rate_cache

    def get_sale_price_in_dollar(self, obj):
        rate = self._get_rate()
        if not rate:
            return None
        return float((obj.sale_price / rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if not request or request.user.role != request.user.UserRoles.MANAGER:
            data.pop("arrival_price", None)
            data.pop("arrival_price_in_dollar", None)

        return data


class QualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Quality
        fields = "__all__"
