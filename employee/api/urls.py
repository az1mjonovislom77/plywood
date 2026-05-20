from django.urls import path
from .views import PaySalaryAPIView, EmployeeSalaryHistoryAPIView, EmployeeSalaryTotalAPIView, \
    EmployeeSalaryMonthlyReportAPIView, AllEmployeesTotalSalaryAPIView

urlpatterns = [
    path("pay/", PaySalaryAPIView.as_view(), name="pay-salary"),
    path("employee/<int:employee_id>/history/", EmployeeSalaryHistoryAPIView.as_view(), name="salary-history"),
    path("employee/<int:employee_id>/monthly/", EmployeeSalaryMonthlyReportAPIView.as_view(), name="salary-monthly"),
    path("employees/totals/", AllEmployeesTotalSalaryAPIView.as_view(), name="all-employees-total"),
]
