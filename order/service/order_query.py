from order.selectors.order_selectors import OrderSelector


class OrderQueryService:
    @staticmethod
    def _base_queryset():
        return OrderSelector.base_queryset()

    @staticmethod
    def list_for_user(user):
        return OrderSelector.list_for_user(user)
