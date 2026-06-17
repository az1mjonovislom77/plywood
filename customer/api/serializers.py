from rest_framework import serializers
from customer.models import Customer, BalanceHistory


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "phone_number", "location", "debt", "overpayment", "about", "description"]
        read_only_fields = ["debt", "overpayment"]


class CoverDebtSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Summa musbat bo'lishi kerak")
        return value


class BalanceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BalanceHistory
        fields = ["id", "type", "amount", "created_at"]


class CustomerHistoryResponseSerializer(serializers.Serializer):
    history = BalanceHistorySerializer(many=True)
    stats = serializers.DictField()


class RefundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Summa musbat bo'lishi kerak")
        return value
