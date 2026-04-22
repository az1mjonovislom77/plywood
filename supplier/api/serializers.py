from rest_framework import serializers
from supplier.models import Supplier, SupplierTransaction
from utils.base.serializers_base import TrimmedDecimalField


class SupplierSerializer(serializers.ModelSerializer):
    daily_acceptance_count = TrimmedDecimalField(max_digits=14, decimal_places=3, read_only=True)
    daily_investment = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id", "full_name", "phone_number", "company", "debt", "is_active",
            "daily_acceptance_count", "daily_investment",
        ]
        read_only_fields = ["debt", "is_active"]


class SupplierTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierTransaction
        fields = ["id", "transaction_type", "amount", "description", "created_at"]


class SupplierPaymentSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
