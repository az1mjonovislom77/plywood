from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from django.utils import timezone
from acceptance.models import CurrencyRate
from product.models import Product, Quality
from utils.base.serializers_base import TrimmedDecimalField


class ProductSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=10, decimal_places=3, read_only=True)
    sale_price_in_dollar = serializers.SerializerMethodField()
    arrival_price_in_dollar = serializers.SerializerMethodField()
    investment_in_dollar = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["arrival_price", "arrival_price_in_dollar", "sale_price", "count", "is_active", "investment_in_dollar"]

    def _get_rate(self):
        if not hasattr(self, "_rate_cache"):
            rate_obj = CurrencyRate.objects.filter(date__lte=timezone.localdate()).order_by("-date").first()
            self._rate_cache = rate_obj.rate if rate_obj else None
        return self._rate_cache

    def get_sale_price_in_dollar(self, obj):
        rate = self._get_rate()
        if not rate or not obj.sale_price:
            return 0
        return float((obj.sale_price / rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        
    def get_arrival_price_in_dollar(self, obj):
        # Agar bazadagi narx to'g'ri bo'lsa, o'shani qaytaramiz
        if obj.arrival_price_in_dollar:
             return float(obj.arrival_price_in_dollar)
             
        # Aks holda, joriy kurs orqali dynamic tarzda hisoblaymiz
        rate = self._get_rate()
        if not rate or not obj.arrival_price:
            return 0
        return float((obj.arrival_price / rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))
        
    def get_investment_in_dollar(self, obj):
        arrival_in_dollar = self.get_arrival_price_in_dollar(obj)
        count = float(obj.count) if obj.count else 0
        return float(count * arrival_in_dollar)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        # Manager bo'lmasa yoki umuman request kelmasa, arrival_price larini yashiramiz
        if not request or getattr(request.user, 'role', None) != getattr(request.user, 'UserRoles', type('roles', (), {'MANAGER': 'manager'})).MANAGER:
            data.pop("arrival_price", None)
            data.pop("arrival_price_in_dollar", None)
            data.pop("investment_in_dollar", None)

        return data


class QualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Quality
        fields = "__all__"
