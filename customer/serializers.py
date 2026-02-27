from rest_framework import serializers
from customer.models import Customer, BalanceHistory


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone_number", "location", "debt", "about", "description"]
        read_only_fields = ["debt"]


class CoverDebtSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class BalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceHistory
        fields = ["id", "type", "amount", "created_at"]


class CustomerHistoryResponseSerializer(serializers.Serializer):
    history = BalanceHistorySerializer(many=True)
    stats = serializers.DictField()
