from decimal import Decimal
from django.db.models import Sum
from customer.models import BalanceHistory, Customer
from order.models import Order, Banding, Cutting


class CustomerBalanceService:

    @staticmethod
    def service_total(service):
        total = service.calculate_price()

        if service.discount > 0:
            if service.discount_type == service.DiscountType.PERCENTAGE:
                total -= total * (service.discount / Decimal("100"))
            else:
                total -= service.discount

        return max(total, Decimal("0"))

    @classmethod
    def sync_customer_debt(cls, customer_id):

        stats = cls.calculate(customer_id)

        Customer.objects.filter(pk=customer_id).update(
            debt=stats["remaining_debt"]
        )

        return stats["remaining_debt"]

    @classmethod
    def calculate(cls, customer_id):

        active_orders = (
            Order.objects
            .filter(customer_id=customer_id)
            .exclude(order_status=Order.OrderStatus.CANCEL)
        )

        orders_total = sum(
            (o.total_price or Decimal("0"))
            for o in active_orders
        )

        orders_paid = sum(
            (o.covered_amount or Decimal("0"))
            for o in active_orders
        )

        cancelled_orders = (
            Order.objects
            .filter(
                customer_id=customer_id,
                order_status=Order.OrderStatus.CANCEL
            )
        )

        cancelled_refund = sum(
            (o.covered_amount or Decimal("0"))
            for o in cancelled_orders
        )

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

        cutting_total = sum(
            cls.service_total(c)
            for c in standalone_cuttings
        )

        cutting_paid = sum((c.covered_amount or Decimal("0")) for c in standalone_cuttings)

        manual_paid = (
                BalanceHistory.objects
                .filter(
                    customer_id=customer_id,
                    type=BalanceHistory.Type.PAYMENT
                )
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0")
        )

        total_orders = (
                orders_total +
                banding_total +
                cutting_total
        )

        total_paid = (
                orders_paid +
                banding_paid +
                cutting_paid +
                manual_paid +
                cancelled_refund
        )

        remaining_debt = total_orders - total_paid

        if remaining_debt < 0:
            remaining_debt = Decimal("0")

        return {
            "total_orders": total_orders,
            "total_paid": total_paid,
            "remaining_debt": remaining_debt,
        }
