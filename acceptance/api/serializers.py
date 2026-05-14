from rest_framework import serializers
from user.models import User
from acceptance.models import Acceptance, AcceptanceHistory
from utils.base.serializers_base import TrimmedDecimalField


class AcceptanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    accepted_by_name = serializers.CharField(source="accepted_by.full_name", read_only=True)
    accepted_at = serializers.DateTimeField(read_only=True)
    history = serializers.SerializerMethodField()
    count = TrimmedDecimalField(max_digits=10, decimal_places=3)
    arrival_price_in_dollar = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    investment = serializers.SerializerMethodField()
    investment_in_dollar = serializers.SerializerMethodField()

    class Meta:
        model = Acceptance
        fields = ["id", "supplier", "product", "price_type", "product_name", "arrival_price", "arrival_price_in_dollar", "sale_price", "count",
                  "arrival_date", "description", "acceptance_status", "accepted_by_name", "accepted_at", "history", "investment", "investment_in_dollar"]

    def get_history(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        user = request.user

        if user.role in [User.UserRoles.MANAGER, User.UserRoles.WAREHOUSEMAN]:
            history = obj.histories.all()
        else:
            return []

        return AcceptanceHistorySerializer(history, many=True, context=self.context).data

    def get_investment(self, obj):
        return obj.count * obj.arrival_price

    def get_investment_in_dollar(self, obj):
        return obj.count * obj.arrival_price_in_dollar


class AcceptanceHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = AcceptanceHistory
        fields = ["id", "user", "acceptance", "supplier", "product", "product_name", "exchange_rate", "price_type",
                  "arrival_price", "sale_price", "count", "arrival_date", "description", "created_at", "action"]


class AcceptanceCancelSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)


class SupplierAcceptanceSerializer(AcceptanceSerializer):
    history = serializers.SerializerMethodField()

    def get_history(self, obj):
        return AcceptanceHistorySerializer(obj.histories.all(), many=True, context=self.context).data


class SupplierStatsSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    supplier_name = serializers.CharField()
    total_quantity = serializers.FloatField()
    total_investment = serializers.FloatField()


class AcceptanceGroupedSerializer(serializers.Serializer):
    date = serializers.DateField()
    suppliers = SupplierStatsSerializer(many=True)