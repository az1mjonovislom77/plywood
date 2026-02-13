from django.db import transaction
from django.db.models import Prefetch

from order.models import Basket, BasketItem


class BasketService:
    @staticmethod
    def get_or_create_basket(user):
        basket, _ = Basket.objects.get_or_create(user=user, is_active=True, defaults={"user": user})

        return basket

    @staticmethod
    def get_basket(user):
        basket = (
            Basket.objects
            .filter(user=user, is_active=True)
            .select_related("user")
            .prefetch_related(Prefetch("items", queryset=BasketItem.objects.select_related("product"))).first()
        )

        if not basket:
            basket = BasketService.get_or_create_basket(user)

        return basket

    @staticmethod
    @transaction.atomic
    def add_product(user, product_id):
        basket = BasketService.get_or_create_basket(user)
        BasketItem.objects.get_or_create(basket=basket, product_id=product_id)

        return BasketService.get_basket(user)

    @staticmethod
    @transaction.atomic
    def remove_product(user, product_id=None):
        basket = BasketService.get_or_create_basket(user)

        if product_id:
            BasketItem.objects.filter(basket=basket, product_id=product_id).delete()
        else:
            basket.items.all().delete()

        return BasketService.get_basket(user)
