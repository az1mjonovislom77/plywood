from rest_framework import serializers
from .models import Supplier, SupplierTransaction


class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = ["id", "full_name", "phone_number", "debt", "is_active"]


class SupplierTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplierTransaction
        fields = ["id", "transaction_type", "amount", "description", "created_at"]


class SupplierPaymentSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)