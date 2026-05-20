from employee.models import Employee
from utils.base.serializers_base import BaseReadSerializer


class EmployeeSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Employee
