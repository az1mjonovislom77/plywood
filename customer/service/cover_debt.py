from django.db import transaction
from django.db.models import F, Sum
from django.core.exceptions import ValidationError
from customer.models import Customer, BalanceHistory

class DebtService:

    @staticmethod
    @transaction.atomic
    def cover_debt(customer_id: int, amount):

        if amount <= 0:
            raise ValidationError("Amount must be positive")

        customer = Customer.objects.select_for_update().get(pk=customer_id)

        Customer.objects.filter(pk=customer_id).update(
            debt=F("debt") - amount,
            covered_debt=F("covered_debt") + amount,
        )

        BalanceHistory.objects.create(customer=customer, type=BalanceHistory.Type.PAYMENT, amount=amount)
        customer.refresh_from_db()
        return customer

    @staticmethod
    def get_customer_history(customer_id: int):
        from order.models import Order, Banding, Cutting

        customer = Customer.objects.get(pk=customer_id)

        history_qs = BalanceHistory.objects.filter(customer_id=customer_id).order_by("-created_at")
        
        main_orders_total = (Order.objects.filter(customer_id=customer_id)
                        .exclude(order_status=Order.OrderStatus.CANCEL)
                        .aggregate(total=Sum("total_price"))["total"] or 0)
                        
        banding_qs = Banding.objects.filter(customer_id=customer_id, orders__isnull=True, order_items__isnull=True)
        cutting_qs = Cutting.objects.filter(customer_id=customer_id, orders__isnull=True, order_items__isnull=True)
        
        # To be perfectly accurate with _service_total:
        def _service_total(instance):
            total = instance.calculate_price()
            if instance.discount > 0:
                if instance.discount_type == instance.DiscountType.PERCENTAGE:
                    from decimal import Decimal
                    total -= total * (instance.discount / Decimal("100"))
                else:
                    total -= instance.discount
            return max(total, 0)
            
        banding_total = sum(_service_total(b) for b in banding_qs)
        cutting_total = sum(_service_total(c) for c in cutting_qs)

        total_orders = main_orders_total + banding_total + cutting_total

        total_paid = (BalanceHistory.objects
                      .filter(customer_id=customer_id,
                              type__in=[BalanceHistory.Type.PAYMENT, BalanceHistory.Type.ORDER_PAYMENT])
                      .aggregate(total=Sum("amount"))["total"] or 0)

        return {
            "history": history_qs,
            "stats": {
                "total_orders": total_orders,
                "total_paid": total_paid,
                "remaining_debt": customer.debt
            }
        }