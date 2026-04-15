from decimal import Decimal
from customer.models import BalanceHistory
from customer.models import Customer
from order.models import OrderItem, Order, Banding, Cutting
from django.db.models.functions import Coalesce
from django.db.models import F, Sum, Value, DecimalField, ExpressionWrapper, Q
from utils.models import Expenses
from supplier.models import SupplierTransaction


class ALlDashboardStatsService:

    @staticmethod
    def _product_gross_expression():
        return ExpressionWrapper(F("price") * F("quantity"),
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
        banding_expr = cls._banding_expression()
        cutting_expr = cls._cutting_expression()

        product_sales = OrderItem.objects.filter(item_filter).aggregate(
            total=Coalesce(
                Sum(product_gross_expr), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        total_discount = Order.objects.filter(order_filter).aggregate(
            total_discount=Coalesce(
                Sum("discount"), Value(Decimal("0.00")),
                output_field=DecimalField(max_digits=14, decimal_places=2))
        )["total_discount"]

        total_debt = Customer.objects.aggregate(
            total=Coalesce(Sum("debt"), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
        )["total"]

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

        debt_payments = BalanceHistory.objects.filter(
            type=BalanceHistory.Type.PAYMENT
        ).aggregate(total=Coalesce(
            Sum("amount"), Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        order_paid_total = Order.objects.filter(order_filter).aggregate(
            total=Coalesce(Sum("covered_amount"), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
        )["total"]

        banding_paid_total = Banding.objects.aggregate(
            total=Coalesce(Sum("covered_amount"), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
        )["total"]

        cutting_paid_total = Cutting.objects.aggregate(
            total=Coalesce(Sum("covered_amount"), Value(Decimal("0.00")),
                           output_field=DecimalField(max_digits=14, decimal_places=2))
        )["total"]

        supplier_payments = SupplierTransaction.objects.filter(
            transaction_type=SupplierTransaction.TransactionType.PAYMENT
        ).aggregate(total=Coalesce(
            Sum("amount"), Value(Decimal("0.00")),
            output_field=DecimalField(max_digits=14, decimal_places=2)))["total"]

        cashbox_total = (
                order_paid_total
                + banding_paid_total
                + cutting_paid_total
                + debt_payments
                - expense_total
                - supplier_payments
        )

        return {
            "cashbox_total": cashbox_total,
            "total_debt": total_debt,
            "total_discount": total_discount,
            "total_product_sales": product_sales,
            "total_banding_sales": banding_income,
            "total_cutting_sales": cutting_income,
        }
