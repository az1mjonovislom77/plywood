from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from employee.models import SalaryPayment, Employee


class SalarySelector:

    @staticmethod
    def get_employee_salary_history(employee_id, month=None):
        queryset = SalaryPayment.objects.filter(employee_id=employee_id).select_related("employee", "paid_by")

        if month:
            year, month_num = map(int, month.split("-"))
        else:
            today = timezone.localdate()
            year = today.year
            month_num = today.month

        queryset = queryset.filter(paid_at__year=year, paid_at__month=month_num)

        return queryset

    @staticmethod
    def get_employee_total_salary(employee_id):
        return SalaryPayment.objects.filter(employee_id=employee_id).aggregate(total=Sum("amount"))["total"] or 0

    @staticmethod
    def get_employee_monthly_report(employee_id):
        return (SalaryPayment.objects.filter(employee_id=employee_id).annotate(month=TruncMonth("paid_at"))
                .values("month").annotate(total=Sum("amount")).order_by("month"))

    @staticmethod
    def get_all_employees_total_salary(month=None):
        queryset = Employee.objects.all()

        if month:
            year, month_num = map(int, month.split("-"))
            queryset = queryset.annotate(
                total_salary=Sum("salary_payments__amount",
                                 filter=Q(
                                     salary_payments__paid_at__year=year,
                                     salary_payments__paid_at__month=month_num)))
        else:
            queryset = queryset.annotate(total_salary=Sum("salary_payments__amount"))

        return queryset
