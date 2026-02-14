from django.db import transaction
from django.db.models import Prefetch
from order.models import Order, OrderItem, Cutting, Banding
from order.service.basket import BasketService


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
    def checkout(user, payment_method, discount=0, discount_type="c", covered_amount=0, banding_data=None,
                 cutting_data=None):

        basket = BasketService.get_basket(user)
        if not basket:
            raise ValueError("Basket not found")

        basket = type(basket).objects.select_for_update().get(id=basket.id)
        basket_items = basket.items.select_related("product")

        if not basket_items.exists():
            raise ValueError("Basket empty")

        banding = None

        if banding_data:
            banding = Banding.objects.create(
                thickness_id=banding_data.get("thickness"),
                width=banding_data.get("width"),
                height=banding_data.get("height"),
            )

        cutting = None

        if cutting_data:
            cutting = Cutting.objects.create(count=cutting_data.get("count"), price=cutting_data.get("price"))

        order = Order.objects.create(
            user=user,
            payment_method=payment_method,
            discount=discount,
            discount_type=discount_type,
            covered_amount=covered_amount,
            banding=banding,
            cutting=cutting,
        )

        OrderItem.objects.bulk_create([
            OrderItem(order=order, product=item.product, price=item.product.sale_price, quantity=1)
            for item in basket_items])

        order.calculate_total()

        basket_items.delete()
        basket.is_active = False
        basket.save(update_fields=["is_active"])

        return order
