from rest_framework import serializers
from product.models import Product, Quality
from utils.base.serializers_base import TrimmedDecimalField


class ProductSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["arrival_price", "sale_price", "count", "is_active"]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if not request or request.user.role != request.user.UserRoles.MANAGER:
            data.pop("arrival_price", None)

        return data


class QualitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Quality
        fields = "__all__"
