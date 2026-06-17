from decimal import Decimal
from collections import defaultdict
from django.db.models import Sum
from django.utils import timezone
from customer.models import BalanceHistory, Customer
from order.models import Order, Banding, Cutting
from utils.models import Services


class CustomerBalanceService:

    @staticmethod
    def service_total(service):
        total = service.calculate_price()

        if service.discount > 0:
            if (service.discount_type == service.DiscountType.PERCENTAGE):
                total -= (total * (service.discount / Decimal("100")))
            else:
                total -= service.discount

        return max(total, Decimal("0"))

    @classmethod
    def sync_customer_debt(cls, customer_id):
        stats = cls.calculate(customer_id)
        remaining_debt = stats["remaining_debt"]
        Customer.objects.filter(pk=customer_id).update(
            debt=max(remaining_debt, Decimal("0")),
            overpayment=max(-remaining_debt, Decimal("0")),
        )

        return stats["remaining_debt"]

    @classmethod
    def calculate(cls, customer_id):

        active_orders = (
            Order.objects
            .filter(customer_id=customer_id)
            .exclude(order_status=Order.OrderStatus.CANCEL))

        orders_total = sum((o.total_price or Decimal("0")) for o in active_orders)
        orders_paid = sum((o.covered_amount or Decimal("0")) for o in active_orders)

        cancelled_orders = (Order.objects.filter(customer_id=customer_id, order_status=Order.OrderStatus.CANCEL))
        cancelled_refund = sum((o.covered_amount or Decimal("0")) for o in cancelled_orders)

        standalone_bandings = (
            Banding.objects
            .filter(
                customer_id=customer_id,
                orders__isnull=True,
                order_items__isnull=True
            )
        )

        banding_total = sum(cls.service_total(b) for b in standalone_bandings)
        banding_paid = sum((b.covered_amount or Decimal("0")) for b in standalone_bandings)
        standalone_cuttings = (
            Cutting.objects
            .filter(
                customer_id=customer_id,
                orders__isnull=True,
                order_items__isnull=True
            )
        )

        cutting_total = sum(cls.service_total(c) for c in standalone_cuttings)
        cutting_paid = sum((c.covered_amount or Decimal("0")) for c in standalone_cuttings)

        standalone_services = Services.objects.filter(customer_id=customer_id)
        services_total = sum(cls.service_total(s) for s in standalone_services)
        services_paid = sum((s.covered_amount or Decimal("0")) for s in standalone_services)

        manual_paid = (
                BalanceHistory.objects
                .filter(customer_id=customer_id, type=BalanceHistory.Type.PAYMENT)
                .aggregate(total=Sum("amount"))["total"] or Decimal("0"))

        total_orders = (
                orders_total +
                banding_total +
                cutting_total +
                services_total
        )

        total_paid = (
                orders_paid +
                banding_paid +
                cutting_paid +
                services_paid +
                manual_paid +
                cancelled_refund
        )

        remaining_debt = (total_orders - total_paid)

        return {
            "total_orders": total_orders,
            "total_paid": total_paid,
            "remaining_debt": remaining_debt,
        }

    @classmethod
    def _sum_by_customer(cls, queryset, field):
        return {
            row["customer_id"]: row["total"] or Decimal("0")
            for row in queryset.values("customer_id").annotate(total=Sum(field))
        }

    @classmethod
    def _service_totals_by_customer(cls, queryset):
        totals = defaultdict(lambda: {"total": Decimal("0"), "paid": Decimal("0")})

        for service in queryset:
            totals[service.customer_id]["total"] += cls.service_total(service)
            totals[service.customer_id]["paid"] += service.covered_amount or Decimal("0")

        return totals

    @classmethod
    def _build_stats(cls, customer_ids, orders, cancelled_orders, bandings, cuttings, services, manual_payments):
        order_total = cls._sum_by_customer(orders, "total_price")
        order_paid = cls._sum_by_customer(orders, "covered_amount")
        cancelled_refund = cls._sum_by_customer(cancelled_orders, "covered_amount")
        manual_paid = cls._sum_by_customer(manual_payments, "amount")
        banding_totals = cls._service_totals_by_customer(bandings)
        cutting_totals = cls._service_totals_by_customer(cuttings)
        services_totals = cls._service_totals_by_customer(services)

        stats = {}
        for customer_id in customer_ids:
            banding = banding_totals[customer_id]
            cutting = cutting_totals[customer_id]
            service = services_totals[customer_id]
            total_orders = (
                order_total.get(customer_id, Decimal("0")) +
                banding["total"] +
                cutting["total"] +
                service["total"]
            )
            total_paid = (
                order_paid.get(customer_id, Decimal("0")) +
                banding["paid"] +
                cutting["paid"] +
                service["paid"] +
                manual_paid.get(customer_id, Decimal("0")) +
                cancelled_refund.get(customer_id, Decimal("0"))
            )

            stats[customer_id] = {
                "total_orders": total_orders,
                "total_paid": total_paid,
                "remaining_debt": total_orders - total_paid,
            }

        return stats

    @classmethod
    def bulk_calculate(cls, customer_ids):
        customer_ids = list(customer_ids)
        if not customer_ids:
            return {}

        active_orders = (
            Order.objects
            .filter(customer_id__in=customer_ids)
            .exclude(order_status=Order.OrderStatus.CANCEL)
        )
        cancelled_orders = Order.objects.filter(
            customer_id__in=customer_ids,
            order_status=Order.OrderStatus.CANCEL,
        )
        standalone_bandings = Banding.objects.filter(
            customer_id__in=customer_ids,
            orders__isnull=True,
            order_items__isnull=True,
        )
        standalone_cuttings = Cutting.objects.filter(
            customer_id__in=customer_ids,
            orders__isnull=True,
            order_items__isnull=True,
        )
        standalone_services = Services.objects.filter(customer_id__in=customer_ids)
        manual_payments = BalanceHistory.objects.filter(
            customer_id__in=customer_ids,
            type=BalanceHistory.Type.PAYMENT,
        )

        return cls._build_stats(
            customer_ids=customer_ids,
            orders=active_orders,
            cancelled_orders=cancelled_orders,
            bandings=standalone_bandings,
            cuttings=standalone_cuttings,
            services=standalone_services,
            manual_payments=manual_payments,
        )

    @classmethod
    def bulk_sync_customer_debts(cls, customer_ids):
        stats = cls.bulk_calculate(customer_ids)

        customers = []
        for customer in Customer.objects.filter(id__in=stats.keys()):
            remaining_debt = stats[customer.id]["remaining_debt"]
            customer.debt = max(remaining_debt, Decimal("0"))
            customer.overpayment = max(-remaining_debt, Decimal("0"))
            customers.append(customer)

        Customer.objects.bulk_update(customers, ["debt", "overpayment"])
        return stats

    @classmethod
    def bulk_calculate_customer_debt(cls, customers, date_from=None, date_to=None):
        from django.utils.dateparse import parse_date

        customers = list(customers)
        customer_ids = [customer.id for customer in customers]
        if not customer_ids:
            return {}

        date_from = parse_date(date_from) if isinstance(date_from, str) else date_from
        date_to = parse_date(date_to) if isinstance(date_to, str) else date_to
        start_dt = timezone.make_aware(timezone.datetime.combine(date_from, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(
            timezone.datetime.combine(date_to + timezone.timedelta(days=1), timezone.datetime.min.time()))

        active_orders = (
            Order.objects
            .filter(customer_id__in=customer_ids, created_at__gte=start_dt, created_at__lt=end_dt)
            .exclude(order_status=Order.OrderStatus.CANCEL)
        )
        cancelled_orders = Order.objects.filter(
            customer_id__in=customer_ids,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            order_status=Order.OrderStatus.CANCEL,
        )
        standalone_bandings = Banding.objects.filter(
            customer_id__in=customer_ids,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            orders__isnull=True,
            order_items__isnull=True,
        )
        standalone_cuttings = Cutting.objects.filter(
            customer_id__in=customer_ids,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            orders__isnull=True,
            order_items__isnull=True,
        )
        standalone_services = Services.objects.filter(
            customer_id__in=customer_ids,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        )
        manual_payments = BalanceHistory.objects.filter(
            customer_id__in=customer_ids,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
            type=BalanceHistory.Type.PAYMENT,
        )

        stats = cls._build_stats(
            customer_ids=customer_ids,
            orders=active_orders,
            cancelled_orders=cancelled_orders,
            bandings=standalone_bandings,
            cuttings=standalone_cuttings,
            services=standalone_services,
            manual_payments=manual_payments,
        )

        return {
            customer_id: customer_stats["remaining_debt"]
            for customer_id, customer_stats in stats.items()
        }

    @classmethod
    def calculate_customer_debt(cls, customer, date_from=None, date_to=None):
        from django.utils.dateparse import parse_date
        date_from = (parse_date(date_from) if isinstance(date_from, str) else date_from)
        date_to = (parse_date(date_to) if isinstance(date_to, str) else date_to)
        start_dt = timezone.make_aware(timezone.datetime.combine(date_from, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(
            timezone.datetime.combine(date_to + timezone.timedelta(days=1), timezone.datetime.min.time()))
        active_orders = (Order.objects
                         .filter(customer=customer, created_at__gte=start_dt, created_at__lt=end_dt)
                         .exclude(order_status=Order.OrderStatus.CANCEL))

        orders_total = sum((o.total_price or Decimal("0")) for o in active_orders)
        orders_paid = sum((o.covered_amount or Decimal("0")) for o in active_orders)
        cancelled_orders = (
            Order.objects
            .filter(
                customer=customer,
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                order_status=Order.OrderStatus.CANCEL
            )
        )

        cancelled_refund = sum((o.covered_amount or Decimal("0")) for o in cancelled_orders)
        standalone_bandings = (
            Banding.objects
            .filter(
                customer=customer,
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                orders__isnull=True,
                order_items__isnull=True
            )
        )

        banding_total = sum(cls.service_total(b) for b in standalone_bandings)
        banding_paid = sum((b.covered_amount or Decimal("0")) for b in standalone_bandings)
        standalone_cuttings = (
            Cutting.objects
            .filter(
                customer=customer,
                created_at__gte=start_dt,
                created_at__lt=end_dt,
                orders__isnull=True,
                order_items__isnull=True
            )
        )

        cutting_total = sum(cls.service_total(c) for c in standalone_cuttings)
        cutting_paid = sum((c.covered_amount or Decimal("0")) for c in standalone_cuttings)

        standalone_services = Services.objects.filter(
            customer=customer,
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        )
        services_total = sum(cls.service_total(s) for s in standalone_services)
        services_paid = sum((s.covered_amount or Decimal("0")) for s in standalone_services)

        manual_paid = (
                BalanceHistory.objects
                .filter(
                    customer=customer,
                    created_at__gte=start_dt,
                    created_at__lt=end_dt,
                    type=BalanceHistory.Type.PAYMENT
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        )

        total_orders = (
                orders_total +
                banding_total +
                cutting_total +
                services_total
        )

        total_paid = (
                orders_paid +
                banding_paid +
                cutting_paid +
                services_paid +
                manual_paid +
                cancelled_refund
        )

        remaining_debt = (total_orders - total_paid)

        return remaining_debt
