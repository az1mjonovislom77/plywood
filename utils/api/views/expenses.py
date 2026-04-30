from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch, Sum
from rest_framework.viewsets import ViewSet
from utils.base.views_base import BaseUserViewSet
from utils.models import Expenses, ExpensesHistory
from utils.api.serializers import ExpenseCreateSerializer, ExpenseListSerializer, \
    ExpenseHistorySerializer
from utils.service.expense_export import CashFlowReportService
from utils.service.expenses_service import ExpensesWorkflowService
from rest_framework import status, viewsets

from utils.service.finance_json import FinanceReportJsonService


@extend_schema(tags=["Expenses"])
class ExpenseViewSet(BaseUserViewSet):
    queryset = (Expenses.objects.select_related("user")
                .prefetch_related(Prefetch("histories", queryset=ExpensesHistory.objects.select_related("user"))))

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCreateSerializer
        return ExpenseListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total_expense = queryset.filter(
            expense_status__in=[Expenses.ExpensesStatus.CREATED, Expenses.ExpensesStatus.ACCEPT]
        ).aggregate(total=Sum("value"))["total"] or 0

        return Response({
            "stats": {
                "total_expense": total_expense},
            "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = ExpensesWorkflowService.create(serializer.validated_data, request.user)

        return Response(ExpenseListSerializer(expense).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        expense = ExpensesWorkflowService.accept(pk, request.user)

        return Response(ExpenseListSerializer(expense).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        description = request.data.get("description")
        expense = ExpensesWorkflowService.cancel(pk, request.user, description)

        return Response(ExpenseListSerializer(expense).data)


@extend_schema(tags=["ExpensesHistory"])
class ExpenseHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExpenseHistorySerializer
    pagination_class = None

    def get_queryset(self):
        queryset = ExpensesHistory.objects.select_related("expense", "user").order_by("-created_at")
        expense_id = self.request.query_params.get("expense")

        if expense_id:
            queryset = queryset.filter(expense_id=expense_id)

        return queryset


@extend_schema(tags=["ExpenseExport"],
               parameters=[
                   OpenApiParameter(name="from", required=False, type=str),
                   OpenApiParameter(name="to", required=False, type=str)])
class CashFlowReportExcelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        file = CashFlowReportService.build_excel(date_from=date_from, date_to=date_to, )

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="cashflow_report.xlsx"'})


@extend_schema(
    tags=["FinanceReport"],
    parameters=[
        OpenApiParameter(name="from", required=False, type=str),
        OpenApiParameter(name="to", required=False, type=str),
    ],
)
class FinanceReportJsonViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        return Response(FinanceReportJsonService.build(
            date_from=request.query_params.get("from"),
            date_to=request.query_params.get("to")))
