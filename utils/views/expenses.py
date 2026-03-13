from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from utils.base.views_base import BaseUserViewSet
from utils.models import Expenses, ExpensesHistory
from utils.serializers import ExpenseCreateSerializer, ExpenseListSerializer, \
    ExpenseHistorySerializer
from utils.service.expenses_service import ExpensesWorkflowService
from rest_framework import status, viewsets
from django.db.models import Sum


@extend_schema(tags=["Expenses"])
class ExpenseViewSet(BaseUserViewSet):
    queryset = Expenses.objects.all().select_related("user")

    def get_serializer_class(self):
        if self.action == "create":
            return ExpenseCreateSerializer
        return ExpenseListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        total_expense = queryset.filter(
            expense_status__in=[Expenses.ExpensesStatus.CREATED, Expenses.ExpensesStatus.ACCEPT]
        ).aggregate(total=Sum("amount"))["total"] or 0

        return Response({
            "stats": {
                "total_expense": total_expense
            }, "data": serializer.data})

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
