from django.db.models import Q
from order.models import Order
from user.models import User


class OrderQueryService:

    @staticmethod
    def list_for_user(user):

        if user.role == User.UserRoles.SELLER:
            return (Order.objects.filter(user=user, source=Order.OrderSource.SELLER)
                    .select_related("customer", "banding", "cutting")
                    .prefetch_related("items__product").order_by("-id"))

        if user.role == User.UserRoles.CASHIER:
            return (Order.objects.filter(
                Q(source=Order.OrderSource.SELLER, order_status=Order.OrderStatus.WAITING) |
                Q(source=Order.OrderSource.CASHIER, user=user))
                    .select_related("customer", "banding", "cutting")
                    .prefetch_related("items__product").order_by("-id"))

        return (
            Order.objects.all()
            .select_related("customer", "banding", "cutting")
            .prefetch_related("items__product")
            .order_by("-id")
        )
