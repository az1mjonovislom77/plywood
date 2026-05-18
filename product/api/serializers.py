from decimal import Decimal, ROUND_HALF_UP
from rest_framework import serializers
from django.utils import timezone
from acceptance.models import CurrencyRate
from product.models import Product, Quality
from utils.base.serializers_base import TrimmedDecimalField


class ProductSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=10, decimal_places=3, read_only=True)
    # Endi arrival_price va sale_price o'zi dollarda, shuning uchun alohida ...in_dollar kerak emas
    # Lekin so'mdagi narxlarni ko'rsatish uchun ...in_sum maydonlarini qo'shamiz
    arrival_price_in_sum = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    sale_price_in_sum = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    investment_in_dollar = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "category", "name", "color", "quality", "image", "width", "height", "thick",
            "arrival_price",  # Bu endi dollardagi narx
            "sale_price",     # Bu ham dollardagi narx
            "arrival_price_in_sum",
            "sale_price_in_sum",
            "count", "arrival_date", "description", "is_active", "investment_in_dollar"
        ]
        read_only_fields = [
            "arrival_price", 
            "sale_price", 
            "arrival_price_in_sum",
            "sale_price_in_sum",
            "count", 
            "is_active", 
            "investment_in_dollar"
        ]

    def get_investment_in_dollar(self, obj):
        arrival_in_dollar = obj.arrival_price or 0 # Endi arrival_price o'zi dollar
        count = obj.count or 0
        return float(count * arrival_in_dollar)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        # Manager bo'lmasa, kelish narxlarini yashiramiz
        if not request or getattr(request.user, 'role', None) != getattr(request.user, 'UserRoles', type('roles', (), {'MANAGER': 'manager'})).MANAGER:
            data.pop("arrival_price", None)
            data.pop("arrival_price_in_sum", None)
            data.pop("investment_in_dollar", None)

        return data


class QualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Quality
        fields = "__all__"