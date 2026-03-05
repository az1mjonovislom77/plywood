from django.db import transaction
from django.db.models import F
from django.utils import timezone
from order.models import Order
from product.models import Product
from user.models import User
from order.models import OrderHistory


class OrderWorkflowService:

    @staticmethod
    @transaction.atomic
    def seller_cancel(order_id, user, description=None):

        if user.role != User.UserRoles.SELLER:
            raise ValueError("Only seller can cancel")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.user_id != user.id:
            raise ValueError("Not your order")

        if order.source != Order.OrderSource.SELLER:
            raise ValueError("Seller cannot cancel cashier order")

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already closed")

        order.order_status = Order.OrderStatus.CANCEL
        order.save(update_fields=["order_status"])

        for item in order.items.select_related("product"):
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CANCEL,
            visible_for=OrderHistory.VisibleFor.SELLER,
            description=description
        )

        return order

    @staticmethod
    @transaction.atomic
    def cashier_accept(order_id, user):

        if user.role != User.UserRoles.CASHIER:
            raise ValueError("Only cashier can accept")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already processed")

        order.order_status = Order.OrderStatus.ACCEPT
        order.accepted_by = user
        order.accepted_at = timezone.now()

        order.save(update_fields=[
            "order_status",
            "accepted_by",
            "accepted_at"
        ])

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.ACCEPT,
            visible_for=OrderHistory.VisibleFor.CASHIER
        )

        return order

    @staticmethod
    @transaction.atomic
    def cashier_cancel(order_id, user, description=None):

        if user.role != User.UserRoles.CASHIER:
            raise ValueError("Only cashier can cancel")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already processed")

        order.order_status = Order.OrderStatus.CANCEL
        order.save(update_fields=["order_status"])

        for item in order.items.select_related("product"):
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CANCEL,
            visible_for=OrderHistory.VisibleFor.CASHIER,
            description=description
        )
        return order
