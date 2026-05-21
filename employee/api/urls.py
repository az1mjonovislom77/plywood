from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PaySalaryAPIView, EmployeeSalaryHistoryAPIView, \
    EmployeeSalaryMonthlyReportAPIView, AllEmployeesTotalSalaryAPIView, EmployeeViewSet

router = DefaultRouter()
router.register('', EmployeeViewSet, basename='employee')

urlpatterns = [
    path("pay/", PaySalaryAPIView.as_view(), name="pay-salary"),
    path("<int:employee_id>/history/", EmployeeSalaryHistoryAPIView.as_view(), name="salary-history"),
    path("<int:employee_id>/monthly/", EmployeeSalaryMonthlyReportAPIView.as_view(), name="salary-monthly"),
    path("totals/", AllEmployeesTotalSalaryAPIView.as_view(), name="all-employees-total"),
    path('', include(router.urls)),
]
