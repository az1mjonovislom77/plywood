from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from django.utils import timezone
from acceptance.models import CurrencyRate
from product.models import Product, Quality
from utils.base.serializers_base import TrimmedDecimalField


class ProductSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=10, decimal_places=3, read_only=True)
    sale_price_in_dollar = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    arrival_price_in_dollar = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    investment_in_dollar = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = [
            "arrival_price", 
            "arrival_price_in_dollar", 
            "sale_price", 
            "sale_price_in_dollar",
            "count", 
            "is_active", 
            "investment_in_dollar"
        ]

    def get_investment_in_dollar(self, obj):
        arrival_in_dollar = obj.arrival_price_in_dollar or 0
        count = obj.count or 0
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