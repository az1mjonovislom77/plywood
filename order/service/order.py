from django.db import transaction
from django.db.models import Prefetch
from order.models import Order, OrderItem, Cutting, Banding, Basket
from order.service.basket import BasketService
from product.models import Product


class OrderService:

    @staticmethod
    def get_all(user):
        return (
            Order.objects
            .filter(user=user)
            .select_related("banding", "cutting")
            .prefetch_related(Prefetch("items", queryset=OrderItem.objects.select_related("product")))
            .order_by("-id"))

    @staticmethod
    def get_by_id(user, order_id):
        return (
            Order.objects
            .filter(user=user, id=order_id)
            .select_related("banding", "cutting")
            .prefetch_related("items__product")
            .first())

    @staticmethod
    @transaction.atomic
    def checkout(user, payment_method, discount=0, discount_type="c", covered_amount=0):

        basket = BasketService.get_basket(user)
        if not basket:
            raise ValueError("Basket not found")

        basket = Basket.objects.select_for_update().get(id=basket.id)
        basket_items = basket.items.select_related("product")

        if not basket_items.exists():
            raise ValueError("Basket empty")

        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            discount=discount,
            discount_type=discount_type,
            covered_amount=covered_amount,
        )

        order_items = []

        for item in basket_items:

            product = item.product
            quantity = 1
            updated = Product.objects.filter(id=product.id, count__gte=quantity).update(count=F("count") - quantity)

            if not updated:
                raise ValueError(f"{product.name} stock not enough")

            order_items.append(OrderItem(order=order, product=product, price=product.sale_price, quantity=quantity))

        OrderItem.objects.bulk_create(order_items)
        order.calculate_total()

        basket_items.delete()
        basket.is_active = False
        basket.save(update_fields=["is_active"])

        return order
