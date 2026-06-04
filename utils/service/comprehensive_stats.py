from datetime import datetime, time, timedelta
from decimal import Decimal
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from customer.models import BalanceHistory, Customer
from employee.models import SalaryPayment
from order.models import Banding, Cutting, Order, OrderItem
from product.models import Product
from supplier.models import Supplier, SupplierTransaction
from utils.models import Expenses, Services


class DateRangeMixin:
    @staticmethod
    def resolve(date_from=None, date_to=None):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today

        if not start_date or not end_date:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        if end_date < start_date:
            raise ValueError("to date must be greater than or equal to from date")

        start_dt = timezone.make_aware(datetime.combine(start_date, time.min))
        end_dt = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min))

        return start_date, end_date, start_dt, end_dt


class MoneyQueryMixin:
    @staticmethod
    def money_field():
        return DecimalField(max_digits=18, decimal_places=2)

    @classmethod
    def zero(cls):
        return Value(Decimal("0.00"), output_field=cls.money_field())

    @classmethod
    def sum(cls, queryset, expression, key="total"):
        return queryset.aggregate(
            **{key: Coalesce(Sum(expression),
                             cls.zero(), output_field=cls.money_field())})[key]

    @classmethod
    def mul(cls, left, right):
        return ExpressionWrapper(F(left) * F(right), output_field=cls.money_field())

    @classmethod
    def sub(cls, left, right):
        return ExpressionWrapper(left - right, output_field=cls.money_field())

    @classmethod
    def nullable(cls, field):
        return Coalesce(F(field), cls.zero(), output_field=cls.money_field())


class DashboardStatsService(DateRangeMixin, MoneyQueryMixin):

    @classmethod
    def _service_sales_expr(cls, prefix: str = ""):
        gross = cls.mul(f"{prefix}length", f"{prefix}thickness")
        discount = cls.nullable(f"{prefix}discount")
        return cls.sub(gross, discount)

    @classmethod
    def _cutting_sales_expr(cls, prefix: str = ""):
        gross = cls.mul(f"{prefix}price", f"{prefix}count")
        discount = cls.nullable(f"{prefix}discount")
        return cls.sub(gross, discount)

    @classmethod
    def _product_sales_expr(cls):
        return cls.mul("price", "quantity")

    @classmethod
    def _product_profit_expr(cls):
        margin = ExpressionWrapper(
            F("price") - F("product__arrival_price"),
            output_field=cls.money_field(),
        )
        return ExpressionWrapper(margin * F("quantity"), output_field=cls.money_field())

    @classmethod
    def _inventory_value_expr(cls):
        return cls.mul("count", "arrival_price")

    @staticmethod
    def _accepted_order_filter():
        return Q(order_status=Order.OrderStatus.ACCEPT)

    @classmethod
    def _range_filter(cls, start_dt, end_dt):
        return Q(created_at__gte=start_dt, created_at__lt=end_dt)

    @classmethod
    def _accepted_order_range_filter(cls, start_dt, end_dt):
        return cls._accepted_order_filter() & cls._range_filter(start_dt, end_dt)

    @classmethod
    def _accepted_order_item_range_filter(cls, start_dt, end_dt):
        return Q(order__order_status=Order.OrderStatus.ACCEPT) & Q(order__created_at__gte=start_dt,
                                                                   order__created_at__lt=end_dt)

    @classmethod
    def _standalone_service_filter(cls, start_dt, end_dt):
        return cls._range_filter(start_dt, end_dt) & Q(order_items__isnull=True, orders__isnull=True)

    @classmethod
    def _cashbox_total(cls, start_dt=None, end_dt=None):
        order_filter = cls._accepted_order_filter()
        balance_filter = Q()
        expense_filter = Q(expense_status__in=[Expenses.ExpensesStatus.CREATED, Expenses.ExpensesStatus.ACCEPT])
        supplier_filter = Q(transaction_type=SupplierTransaction.TransactionType.PAYMENT)
        banding_filter = Q()
        cutting_filter = Q()
        salary_filter = Q()
        services_filter = Q()

        if start_dt and end_dt:
            date_filter = cls._range_filter(start_dt, end_dt)
            order_filter &= date_filter
            balance_filter &= date_filter
            expense_filter &= date_filter
            supplier_filter &= date_filter
            banding_filter &= date_filter
            cutting_filter &= date_filter
            salary_filter &= Q(paid_at__gte=start_dt, paid_at__lt=end_dt)
            services_filter &= date_filter

        elif end_dt:
            date_filter = Q(created_at__lt=end_dt)
            order_filter &= date_filter
            balance_filter &= date_filter
            expense_filter &= date_filter
            supplier_filter &= date_filter
            banding_filter &= date_filter
            cutting_filter &= date_filter
            salary_filter &= Q(paid_at__lt=end_dt)
            services_filter &= date_filter

        elif start_dt:
            date_filter = Q(created_at__gte=start_dt)
            order_filter &= date_filter
            balance_filter &= date_filter
            expense_filter &= date_filter
            supplier_filter &= date_filter
            banding_filter &= date_filter
            cutting_filter &= date_filter
            salary_filter &= Q(paid_at__gte=start_dt)
            services_filter &= date_filter

        order_paid = cls.sum(Order.objects.filter(order_filter), "covered_amount")
        banding_paid = cls.sum(Banding.objects.filter(banding_filter), "covered_amount")
        cutting_paid = cls.sum(Cutting.objects.filter(cutting_filter), "covered_amount")

        debt_paid = cls.sum(
            BalanceHistory.objects.filter(
                balance_filter,
                type=BalanceHistory.Type.PAYMENT
            ),
            "amount"
        )

        expenses = cls.sum(Expenses.objects.filter(expense_filter), "value")
        supplier_payments = cls.sum(SupplierTransaction.objects.filter(supplier_filter), "amount")
        salary_payments = cls.sum(SalaryPayment.objects.filter(salary_filter), "amount")
        services_total = cls.sum(Services.objects.filter(services_filter), "total_price")

        return (
                order_paid
                + banding_paid
                + cutting_paid
                + debt_paid
                + services_total
                - expenses
                - supplier_payments
                - salary_payments
        )

    @classmethod
    def _get_sales_stats(cls, start_dt, end_dt):
        order_item_filter = cls._accepted_order_item_range_filter(start_dt, end_dt)
        order_filter = cls._accepted_order_range_filter(start_dt, end_dt)
        product_sales = cls.sum(OrderItem.objects.filter(order_item_filter), cls._product_sales_expr())
        product_profit = cls.sum(OrderItem.objects.filter(order_item_filter), cls._product_profit_expr())
        standalone_banding_filter = cls._standalone_service_filter(start_dt, end_dt)
        standalone_cutting_filter = cls._standalone_service_filter(start_dt, end_dt)
        banding_sales = (
                cls.sum(OrderItem.objects.filter(order_item_filter, banding__isnull=False),
                        cls._service_sales_expr("banding__"))
                + cls.sum(
            Order.objects.filter(order_filter, banding__isnull=False, banding__order_items__isnull=True),
            cls._service_sales_expr("banding__"))
                + cls.sum(Banding.objects.filter(standalone_banding_filter), cls._service_sales_expr()))

        cutting_sales = (
                cls.sum(
                    OrderItem.objects.filter(order_item_filter, cutting__isnull=False),
                    cls._cutting_sales_expr("cutting__"))
                + cls.sum(
            Order.objects.filter(order_filter, cutting__isnull=False, cutting__order_items__isnull=True),
            cls._cutting_sales_expr("cutting__"),
        ) + cls.sum(Cutting.objects.filter(standalone_cutting_filter), cls._cutting_sales_expr()))

        return {
            "product_sales": product_sales,
            "product_profit": product_profit,
            "banding_sales": banding_sales,
            "cutting_sales": cutting_sales,
            "total_sales": product_sales + banding_sales + cutting_sales,
            "net_profit": product_profit + banding_sales + cutting_sales,
        }

    @classmethod
    def _get_payment_stats(cls, start_dt, end_dt):
        order_filter = cls._accepted_order_range_filter(start_dt, end_dt)
        standalone_banding_filter = cls._standalone_service_filter(start_dt, end_dt)
        standalone_cutting_filter = cls._standalone_service_filter(start_dt, end_dt)
        sales_by_payment = Order.objects.filter(order_filter).aggregate(
            cash=Coalesce(
                Sum(
                    "covered_amount",
                    filter=Q(
                        payment_method__in=[
                            Order.PaymentMethod.CASH,
                            Order.PaymentMethod.NASIYA,
                        ])), cls.zero(), output_field=cls.money_field()),
            card=Coalesce(Sum("covered_amount", filter=Q(payment_method=Order.PaymentMethod.CARD)),
                          cls.zero(), output_field=cls.money_field()))

        banding_payment = Banding.objects.filter(standalone_banding_filter).aggregate(
            cash=Coalesce(Sum("covered_amount",
                              filter=Q(
                                  payment_method__in=[
                                      Banding.PaymentMethod.CASH,
                                      Banding.PaymentMethod.NASIYA])),
                          cls.zero(), output_field=cls.money_field()),
            card=Coalesce(
                Sum("covered_amount", filter=Q(payment_method=Banding.PaymentMethod.CARD)),
                cls.zero(), output_field=cls.money_field()))

        cutting_payment = Cutting.objects.filter(standalone_cutting_filter).aggregate(
            cash=Coalesce(Sum("covered_amount",
                              filter=Q(
                                  payment_method__in=[
                                      Cutting.PaymentMethod.CASH,
                                      Cutting.PaymentMethod.NASIYA,
                                  ])), cls.zero(), output_field=cls.money_field()),
            card=Coalesce(
                Sum("covered_amount",
                    filter=Q(payment_method=Cutting.PaymentMethod.CARD)),
                cls.zero(),
                output_field=cls.money_field()))

        return {
            "cash_sales": (
                    sales_by_payment["cash"]
                    + banding_payment["cash"]
                    + cutting_payment["cash"]
            ),
            "card_sales": (
                    sales_by_payment["card"]
                    + banding_payment["card"]
                    + cutting_payment["card"]
            ),
        }

    @classmethod
    def _get_debt_stats(cls, start_dt, end_dt):
        stats = (BalanceHistory.objects.filter(cls._range_filter(start_dt, end_dt))
        .aggregate(
            paid=Coalesce(Sum("amount", filter=Q(type=BalanceHistory.Type.PAYMENT)),
                          cls.zero(), output_field=cls.money_field()),
            added=Coalesce(Sum("amount", filter=Q(type=BalanceHistory.Type.DEBT_ADD)),
                           cls.zero(), output_field=cls.money_field())))

        return {
            "paid_debt": stats["paid"],
            "added_debt": stats["added"],
            "total_customer_debt": cls.sum(Customer.objects.all(), "debt"),
            "total_supplier_debt": cls.sum(Supplier.objects.all(), "debt"),
        }

    @classmethod
    def _get_inventory_stats(cls):
        return {
            "inventory_arrival_value": cls.sum(
                Product.objects.filter(is_active=True, count__gt=0),
                cls._inventory_value_expr(),
            )
        }

    @classmethod
    def _get_expense_stats(cls, start_dt, end_dt):
        expenses = cls.sum(
            Expenses.objects.filter(
                cls._range_filter(start_dt, end_dt),
                expense_status__in=[Expenses.ExpensesStatus.CREATED, Expenses.ExpensesStatus.ACCEPT]), "value")
        return {"daily_expense": expenses}

    @classmethod
    def get_stats(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = cls.resolve(date_from, date_to)
        sales = cls._get_sales_stats(start_dt, end_dt)
        payments = cls._get_payment_stats(start_dt, end_dt)
        debts = cls._get_debt_stats(start_dt, end_dt)
        inventory = cls._get_inventory_stats()
        expenses = cls._get_expense_stats(start_dt, end_dt)

        return {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "cashbox_total": float(cls._cashbox_total()),
            "daily_cash": float(cls._cashbox_total(start_dt, end_dt)),

            **{k: float(v) for k, v in debts.items()},
            **{k: float(v) for k, v in expenses.items()},
            **{k: float(v) for k, v in payments.items()},
            **{k: float(v) for k, v in inventory.items()},
            **{k: float(v) for k, v in sales.items()},
        }
