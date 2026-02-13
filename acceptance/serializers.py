from rest_framework import serializers
from .models import Acceptance, AcceptanceHistory


class AcceptanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Acceptance
        fields = ["id", "product", "product_name", "arrival_price", "sale_price", "count", "arrival_date",
                  "description"]


class AcceptanceHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = AcceptanceHistory
        fields = ["id", "acceptance", "product", "product_name", "arrival_price", "sale_price", "count", "arrival_date",
                  "description", "created_at"]
