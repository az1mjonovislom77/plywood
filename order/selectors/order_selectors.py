from django.db.models import Prefetch, Q

from order.models import Order, OrderHistory
from user.models import User


class OrderSelector:
    @staticmethod
    def base_queryset():
        return (
            Order.objects.select_related(
                "customer", "banding", "banding__thickness", "banding__customer", "cutting", "cutting__customer",
                "accepted_by", "user",
            )
            .prefetch_related("items__product", "items__banding", "items__banding__thickness",
                              "items__banding__customer", "items__cutting", "items__cutting__customer",
                              Prefetch("history", queryset=OrderHistory.objects.select_related("user")))
        )

    # @staticmethod
    # def list_for_user(user):
    #     queryset = OrderSelector.base_queryset()
    #
    #     if user.role == User.UserRoles.SELLER:
    #         return queryset.filter(user=user, source=Order.OrderSource.SELLER).order_by("-id")
    #
    #     if user.role == User.UserRoles.CASHIER:
    #         return (
    #             queryset.filter(
    #                 Q(source=Order.OrderSource.SELLER, order_status=Order.OrderStatus.WAITING)
    #                 | Q(source=Order.OrderSource.CASHIER, user=user)
    #             ).order_by("-id")
    #         )
    #
    #     return queryset.order_by("-id")

    @staticmethod
    def list_for_user(user):
        queryset = OrderSelector.base_queryset()
        return queryset.order_by("-id")
