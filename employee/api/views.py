from drf_spectacular.utils import extend_schema
from employee.models import Employee
from employee.api.serializers import EmployeeSerializer
from utils.base.views_base import BaseUserViewSet
from utils.search import TransliteratedSearchFilter


@extend_schema(tags=["Employee"])
class EmployeeViewSet(BaseUserViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["full_name"]
    ordering = ["full_name"]
