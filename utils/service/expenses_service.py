import logging
from django.db import transaction
from utils.models import Expenses, ExpensesHistory
from utils.service.comprehensive_stats import DashboardStatsService

logger = logging.getLogger(__name__)


class ExpensesWorkflowService:
    LIMIT = 1_000_000

    @staticmethod
    @transaction.atomic
    def create(data, user):
        value = data.get("value", 0)
        if value >= ExpensesWorkflowService.LIMIT:
            status = Expenses.ExpensesStatus.WAITING
        else:
            status = Expenses.ExpensesStatus.CREATED

        if status == Expenses.ExpensesStatus.CREATED:
            ExpensesWorkflowService._apply_cashbox(value)

        expense = Expenses.objects.create(user=user, value=value, description=data.get("description"),
                                          type=data.get("type", Expenses.ExpensesType.BOSHQA),
                                          expense_status=status)

        ExpensesHistory.objects.create(expense=expense, user=user, action=ExpensesHistory.Action.CREATE,
                                       value=expense.value, description=expense.description)
        logger.info("Expense #%s created by user %s (value: %s, status: %s)", expense.id, user.id, value, status)
        return expense

    @staticmethod
    def _apply_cashbox(value):
        stats = DashboardStatsService.get_stats()

        if stats["cashbox_total"] < value:
            raise ValueError("Cashboxda yetarli mablag yo'q")

    @staticmethod
    @transaction.atomic
    def accept(expense_id, user):
        expense = Expenses.objects.select_for_update().get(id=expense_id)
        if expense.expense_status != Expenses.ExpensesStatus.WAITING:
            raise ValueError("Xarajat allaqachon qayta ishlangan")

        ExpensesWorkflowService._apply_cashbox(expense.value)
        expense.expense_status = Expenses.ExpensesStatus.ACCEPT
        expense.save(update_fields=["expense_status"])
        ExpensesHistory.objects.create(expense=expense, user=user, action=ExpensesHistory.Action.ACCEPT,
                                       value=expense.value, description=expense.description)

        return expense

    @staticmethod
    @transaction.atomic
    def cancel(expense_id, user, description=None):
        expense = Expenses.objects.select_for_update().get(id=expense_id)
        if expense.expense_status != Expenses.ExpensesStatus.WAITING:
            raise ValueError("Xarajat allaqachon qayta ishlangan")

        expense.expense_status = Expenses.ExpensesStatus.CANCEL
        expense.save(update_fields=["expense_status"])
        ExpensesHistory.objects.create(expense=expense, user=user, action=ExpensesHistory.Action.CANCEL,
                                       value=expense.value, description=description)

        return expense
