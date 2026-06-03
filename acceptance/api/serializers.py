from rest_framework import serializers
from acceptance.models import Acceptance, AcceptanceHistory
from utils.base.serializers_base import TrimmedDecimalField


class AcceptanceSerializer(serializers.ModelSerializer):
    count = TrimmedDecimalField(max_digits=20, decimal_places=3)
    product_name = serializers.CharField(source="product.name", read_only=True)
    accepted_by_name = serializers.CharField(source="accepted_by.username", read_only=True)
    history = serializers.SerializerMethodField()
    investment = serializers.SerializerMethodField()
    investment_in_dollar = serializers.SerializerMethodField()
    arrival_price_in_dollar = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    arrival_price_in_sum = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    sale_price_in_dollar = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)
    sale_price_in_sum = serializers.DecimalField(max_digits=20, decimal_places=2, read_only=True)

    class Meta:
        model = Acceptance
        fields = ["id", "supplier", "product", "price_type", "product_name", "arrival_price", "arrival_price_in_dollar",
                  "arrival_price_in_sum", "sale_price", "sale_price_in_dollar", "sale_price_in_sum", "count",
                  "arrival_date", "description", "acceptance_status", "accepted_by_name", "accepted_at", "history",
                  "investment", "investment_in_dollar"]
        read_only_fields = ["acceptance_status"]

    def get_investment(self, obj):
        return obj.count * obj.arrival_price

    def get_investment_in_dollar(self, obj):
        return obj.count * obj.arrival_price_in_dollar

    def get_history(self, obj):
        history = obj.histories.all()
        return AcceptanceHistorySerializer(history, many=True, context=self.context).data

    def to_representation(self, instance):
        data = super().to_representation(instance)

        request = self.context.get("request")

        if not request or getattr(request.user, 'role', None) != getattr(request.user, 'UserRoles', type('roles', (), {
            'MANAGER': 'manager'})).MANAGER:
            data.pop("arrival_price", None)
            data.pop("arrival_price_in_dollar", None)
            data.pop("arrival_price_in_sum", None)
            data.pop("investment", None)
            data.pop("investment_in_dollar", None)

        return data


class AcceptanceHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    count = TrimmedDecimalField(max_digits=20, decimal_places=3)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = AcceptanceHistory
        fields = ["id", "user", "acceptance", "supplier", "product", "product_name", "exchange_rate", "price_type",
                  "arrival_price", "sale_price", "count", "arrival_date", "description", "created_at", "action"]


class AcceptanceCancelSerializer(serializers.Serializer):
    description = serializers.CharField(required=True)


class SupplierAcceptanceSerializer(AcceptanceSerializer):
    def get_history(self, obj):
        return AcceptanceHistorySerializer(obj.histories.all(), many=True, context=self.context).data


class AcceptanceGroupedSerializer(serializers.Serializer):
    date = serializers.DateField()
    suppliers = serializers.ListField()
