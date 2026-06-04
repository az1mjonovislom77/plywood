from rest_framework.fields import SerializerMethodField
from utils.base.serializers_base import BaseReadSerializer
from utils.models import Currency, Expenses, ExpensesHistory, Services
from rest_framework import serializers
from user.models import User


class CurrencySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Currency


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expenses
        fields = ["id", "value", "description"]


class ExpenseHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = ExpensesHistory
        fields = ["id", "expense", "user", "action", "value", "description", "created_at"]


class ExpenseListSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    history = SerializerMethodField()

    class Meta:
        model = Expenses
        fields = ["id", "user", "value", "description", "expense_status", "history", "created_at"]

    def get_history(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        user = request.user

        if user.role in [User.UserRoles.MANAGER, User.UserRoles.WAREHOUSEMAN]:
            history = obj.histories.all()
        else:
            return []

        return ExpenseHistorySerializer(history, many=True, context=self.context).data


class ServicesSerializer(serializers.ModelSerializer):
    services_name = serializers.CharField(source="services_name.name", read_only=True)
    services_id = serializers.IntegerField(source="services_name.id")
    total_price = SerializerMethodField()

    class Meta:
        model = Services
        fields = "__all__"

    def get_total_price(self, obj):
        return obj.count * obj.price
