from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.base.views_base import BaseUserViewSet
from utils.search import TransliteratedSearchFilter
from .serializers import SalaryPaymentCreateSerializer, SalaryPaymentSerializer, EmployeeSalaryTotalSerializer, \
    EmployeeSerializer
from ..models import Employee
from ..selectors.employee import SalarySelector
from ..service.pay_salary import PaySalaryService


@extend_schema(tags=["Employee"])
class SupplierViewSet(BaseUserViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ["full_name"]
    ordering = ["full_name"]


@extend_schema(tags=["Salary"], request=SalaryPaymentCreateSerializer, responses={201: SalaryPaymentSerializer})
class PaySalaryAPIView(APIView):

    def post(self, request):
        serializer = SalaryPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = PaySalaryService.pay_salary(
            employee_id=serializer.validated_data["employee_id"],
            amount=serializer.validated_data["amount"],
            paid_by=request.user
        )

        return Response(SalaryPaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Salary"],
               parameters=[OpenApiParameter(name="employee_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH)],
               responses={200: SalaryPaymentSerializer(many=True)})
class EmployeeSalaryHistoryAPIView(APIView):

    def get(self, request, employee_id):
        payments = SalarySelector.get_employee_salary_history(employee_id)
        serializer = SalaryPaymentSerializer(payments, many=True)

        return Response(serializer.data)


@extend_schema(tags=["Salary"],
               parameters=[OpenApiParameter(name="employee_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH)])
class EmployeeSalaryTotalAPIView(APIView):

    def get(self, request, employee_id):
        total = SalarySelector.get_employee_total_salary(employee_id)

        return Response({"employee_id": employee_id, "total_salary": total})


@extend_schema(tags=["Salary"],
               parameters=[OpenApiParameter(
                   name="employee_id", type=OpenApiTypes.INT, location=OpenApiParameter.PATH)])
class EmployeeSalaryMonthlyReportAPIView(APIView):

    def get(self, request, employee_id):
        report = SalarySelector.get_employee_monthly_report(employee_id)

        return Response(report)


@extend_schema(tags=["Salary"],
               parameters=[OpenApiParameter(
                   name="month", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False,
                   description="Format: YYYY-MM")],
               responses={200: EmployeeSalaryTotalSerializer(many=True)})
class AllEmployeesTotalSalaryAPIView(APIView):

    def get(self, request):
        month = request.query_params.get("month")

        employees = SalarySelector.get_all_employees_total_salary(month=month)
        serializer = EmployeeSalaryTotalSerializer(employees, many=True)

        return Response(serializer.data)
