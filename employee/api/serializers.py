from rest_framework import serializers

from employee.models import SalaryPayment, Employee


class SalaryPaymentCreateSerializer(serializers.Serializer):
    employee_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class SalaryPaymentSerializer(serializers.ModelSerializer):
    employee = serializers.StringRelatedField()
    paid_by = serializers.StringRelatedField()

    class Meta:
        model = SalaryPayment
        fields = ["id", "employee", "amount", "paid_at", "paid_by"]


class EmployeeSalaryTotalSerializer(serializers.ModelSerializer):
    total_salary = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = ["id", "full_name", "total_salary"]

    def get_total_salary(self, obj):
        return obj.total_salary or 0
