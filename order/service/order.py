from django.db import transaction
from django.db.models import F
from customer.models import Customer
from customer.models import BalanceHistory
from order.models import Order, OrderItem, Cutting, Banding, Basket
from order.service.basket import BasketService
from product.models import Product
from order.models import OrderHistory
from user.models import User


class OrderService:

    @staticmethod
    def get_by_id(order_id):
        return (Order.objects
                .filter(id=order_id)
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

        items_map = {item["product_id"]: item["quantity"] for item in items}

        basket_product_ids = set(basket_items.values_list("product_id", flat=True))

        for product_id in items_map.keys():
            if product_id not in basket_product_ids:
                raise ValueError("Product not in basket")

        banding = Banding.objects.create(**banding_data) if banding_data else None
        cutting = Cutting.objects.create(**cutting_data) if cutting_data else None

        customer = None
        if customer_id:
            try:
                customer = Customer.objects.get(id=customer_id)
            except Customer.DoesNotExist:
                raise ValueError("Customer not found")
        source = (Order.OrderSource.CASHIER
                  if user.role == user.UserRoles.CASHIER
                  else Order.OrderSource.SELLER)

        order = Order.objects.create(
            user=user,
            source=source,
            customer=customer,
            is_anonymous=(customer is None),
            payment_method=payment_method,
            discount=discount,
            discount_type=discount_type,
            covered_amount=covered_amount,
            banding=banding,
            cutting=cutting
        )

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CREATE,
            visible_for=(
                OrderHistory.VisibleFor.CASHIER
                if user.role == User.UserRoles.CASHIER
                else OrderHistory.VisibleFor.SELLER
            )
        )
        order_items = []
        created_product_ids = []

        for basket_item in basket_items:
            product = basket_item.product
            quantity = items_map.get(product.id)

            if quantity is None:
                continue

            if quantity <= 0:
                raise ValueError("Invalid quantity")

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

        remaining = order.total_price - order.covered_amount

        if order.customer:

            customer = Customer.objects.select_for_update().get(id=order.customer.id)

            if order.covered_amount > 0:
                BalanceHistory.objects.create(customer=customer, type=BalanceHistory.Type.PAYMENT,
                                              amount=order.covered_amount)

            if order.payment_method == Order.PaymentMethod.NASIYA and remaining > 0:
                Customer.objects.filter(id=customer.id).update(debt=F("debt") + remaining)
                BalanceHistory.objects.create(customer=customer, type=BalanceHistory.Type.DEBT_ADD, amount=remaining)

        if not basket.items.exists():
            basket.is_active = False
            basket.save(update_fields=["is_active"])

        return (Order.objects.select_related("customer", "banding", "cutting")
                .prefetch_related("items__product").get(id=order.id))
