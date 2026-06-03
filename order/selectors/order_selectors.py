from django.db.models import Prefetch
from order.models import Order, OrderHistory


class OrderSelector:
    @staticmethod
    def base_queryset():
        return (
            Order.objects.select_related(
                "customer", "banding", "banding__customer", "cutting", "cutting__customer",
                "accepted_by", "user",
            )
            .prefetch_related("items__product", "items__banding",
                              "items__banding__customer", "items__cutting", "items__cutting__customer",
                              Prefetch("history", queryset=OrderHistory.objects.select_related("user")))
        )

    @staticmethod
    def list_for_user(user):
        queryset = OrderSelector.base_queryset()
        return queryset.order_by("-id")
