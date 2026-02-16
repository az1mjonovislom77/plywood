from django.db import transaction
from django.db.models import Prefetch, F
from customer.models import Customer
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
    def checkout(user, payment_method, items, customer_id=None, covered_amount=0, discount=0, discount_type="c",
                 banding_data=None, cutting_data=None):

        basket = BasketService.get_basket(user)
        if not basket:
            raise ValueError("Basket not found")

        basket = Basket.objects.select_for_update().get(id=basket.id)
        basket_items = basket.items.select_related("product")

        if not basket_items.exists():
            raise ValueError("Basket empty")

        items_map = {item["product_id"]: item["quantity"]
                     for item in items}

        banding = Banding.objects.create(**banding_data) if banding_data else None
        cutting = Cutting.objects.create(**cutting_data) if cutting_data else None

        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                raise ValueError("Customer not found")

        order = Order.objects.create(
            user=user,
            customer=customer,
            payment_method=payment_method,
            discount=discount,
            discount_type=discount_type,
            covered_amount=covered_amount,
            banding=banding,
            cutting=cutting
        )

        order_items = []
        created_product_ids = []

        for basket_item in basket_items:
            product = basket_item.product
            quantity = items_map.get(product.id)

            if quantity is None:
                continue

            updated = Product.objects.filter(id=product.id, count__gte=quantity).update(count=F("count") - quantity)

            if not updated:
                raise ValueError(f"{product.name} stock not enough")

            order_items.append(OrderItem(order=order, product=product, quantity=quantity, price=product.sale_price))
            created_product_ids.append(product.id)

        OrderItem.objects.bulk_create(order_items)

        basket.items.filter(product_id__in=created_product_ids).delete()

        order.calculate_total()
        order.full_clean()
        order.save(update_fields=["total_price"])

        if order.payment_method == Order.PaymentMethod.NASIYA:

            if not order.customer:
                raise ValueError("Customer required for nasiya payment")

            remaining = order.total_price - order.covered_amount

            if remaining > 0:
                order.customer.increase_debt(remaining)

        if not basket.items.exists():
            basket.is_active = False
            basket.save(update_fields=["is_active"])

        return (Order.objects.select_related("customer", "banding", "cutting")
                .prefetch_related("items__product").get(id=order.id))
