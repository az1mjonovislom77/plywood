from decimal import Decimal
from django.db.models import Sum
from customer.models import BalanceHistory
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
    def calculate(cls, customer_id):

        active_orders = (
            Order.objects
            .filter(customer_id=customer_id)
            .exclude(order_status=Order.OrderStatus.CANCEL)
        )

        orders_total = sum(
            o.total_price or Decimal("0")
            for o in active_orders
        )

        standalone_bandings = (
            Banding.objects
            .filter(
                customer_id=customer_id,
                orders__isnull=True,
                order_items__isnull=True
            )
        )

        banding_total = sum(
            cls.service_total(b)
            for b in standalone_bandings
        )

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

        total_orders = (
            orders_total +
            banding_total +
            cutting_total
        )

        total_paid = (
            BalanceHistory.objects
            .filter(
                customer_id=customer_id,
                type__in=[
                    BalanceHistory.Type.PAYMENT,
                    BalanceHistory.Type.ORDER_PAYMENT,
                ]
            )
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0")
        )

        remaining_debt = total_orders - total_paid

        return {
            "total_orders": total_orders,
            "total_paid": total_paid,
            "remaining_debt": remaining_debt,
        }