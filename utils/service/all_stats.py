from decimal import Decimal
from order.models import OrderItem, Order, Banding, Cutting
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q
from utils.models import Expenses


class ALlDashboardStatsService:

    @staticmethod
    def _product_gross_expression():
        return ExpressionWrapper(F("price") * F("quantity"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @staticmethod
    def _debt_expression():
        return ExpressionWrapper(
            F("total_price") - Coalesce(F("covered_amount"), Value(0)),
            output_field=DecimalField(max_digits=14, decimal_places=2))

    @staticmethod
    def _banding_expression():
        return ExpressionWrapper(F("length") * F("thickness__price"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @staticmethod
    def _cutting_expression():
        return ExpressionWrapper(F("price") * F("count"),
                                 output_field=DecimalField(max_digits=14, decimal_places=2))

    @classmethod
    def get_all_stats(cls):
        item_filter = Q(
            order__order_status=Order.OrderStatus.ACCEPT)

        order_filter = Q(
            order_status=Order.OrderStatus.ACCEPT)

        expense_filter = Q(
            expense_status__in=[Expenses.ExpensesStatus.CREATED, Expenses.ExpensesStatus.ACCEPT])

        product_gross_expr = cls._product_gross_expression()
        debt_expr = cls._debt_expression()
        banding_expr = cls._banding_expression()
        cutting_expr = cls._cutting_expression()

        product_sales = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_gross_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        order_stats = Order.objects.filter(order_filter).aggregate(
            total_debt=Coalesce(
                Sum(debt_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)),

            total_discount=Coalesce(
                Sum("discount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))

        total_debt = order_stats["total_debt"]
        total_discount = order_stats["total_discount"]

        banding_income = Banding.objects.select_related("thickness").aggregate(
            total=Coalesce(
                Sum(banding_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cutting_income = Cutting.objects.all().aggregate(
            total=Coalesce(
                Sum(cutting_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        expense_total = Expenses.objects.filter(expense_filter).aggregate(
            total=Coalesce(
                Sum("value"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cashbox_total = (
                product_sales
                + banding_income
                + cutting_income
                - total_discount
                - total_debt
                - expense_total
        )

        return {
            "cashbox_total": cashbox_total,
            "total_debt": total_debt
        }
