from rest_framework import serializers

from user.models import User
from .models import Acceptance, AcceptanceHistory


class AcceptanceSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    accepted_by_name = serializers.CharField(source="accepted_by.full_name", read_only=True)
    accepted_at = serializers.DateTimeField(read_only=True)
    history = serializers.SerializerMethodField()

    class Meta:
        model = Acceptance
        fields = ["id", "supplier", "product", "price_type", "product_name", "arrival_price", "sale_price", "count",
                  "arrival_date", "description", "acceptance_status", "accepted_by_name", "accepted_at", "history"]

    def get_history(self, obj):
        request = self.context.get("request")
        if not request:
            return None

        user = request.user

        if user.role in [User.UserRoles.MANAGER, User.UserRoles.WAREHOUSEMAN]:
            history = getattr(obj, "history", None)
        else:
            history = None

        if not history:
            return None

        return AcceptanceHistorySerializer(history, context=self.context).data


class AcceptanceHistorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = AcceptanceHistory
        fields = ["id", "user", "acceptance", "supplier", "product", "product_name", "exchange_rate", "price_type",
                  "arrival_price", "sale_price", "count", "arrival_date", "description", "created_at", "action"]


class AcceptanceCancelSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)
