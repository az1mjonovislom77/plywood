from utils.base.serializers_base import BaseReadSerializer
from utils.models import Currency, Expenses
from rest_framework import serializers


class CurrencySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Currency


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ["id", "value", "description"]


class ExpenseListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Expenses
        fields = ["id", "user", "value", "description", "expense_status", "created_at"]
