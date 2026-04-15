from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from customer.models import BalanceHistory, Customer
from order.models import Banding, Basket, Cutting, Order, OrderHistory, OrderItem
from order.service.basket import BasketService
from product.models import Product
from user.models import User


class OrderService:
    @staticmethod
    def _get_customer(customer_id):
        if not customer_id:
            return None

        try:
            return Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist as exc:
            raise ValueError("Customer not found") from exc

    @staticmethod
    def _calculate_service_total(instance):
        total = instance.calculate_price()

        if instance.discount > 0:
            if instance.discount_type == instance.DiscountType.PERCENTAGE:
                total -= total * (instance.discount / Decimal("100"))
            else:
                total -= instance.discount

        return max(total, Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _apply_customer_balance(instance):
        total = OrderService._calculate_service_total(instance)

        if instance.payment_method != instance.PaymentMethod.NASIYA:
            instance.covered_amount = total

        instance.full_clean()
        instance.save()

        remaining = total - instance.covered_amount

        if not instance.customer:
            return instance

        customer = Customer.objects.select_for_update().get(id=instance.customer_id)

        if instance.covered_amount > 0:
            BalanceHistory.objects.create(
                customer=customer,
                type=BalanceHistory.Type.ORDER_PAYMENT,
                amount=instance.covered_amount,
            )

        if instance.payment_method == instance.PaymentMethod.NASIYA and remaining > 0:
            Customer.objects.filter(id=customer.id).update(debt=F("debt") + remaining)
            BalanceHistory.objects.create(
                customer=customer,
                type=BalanceHistory.Type.DEBT_ADD,
                amount=remaining,
            )

        return instance

    @staticmethod
    def get_by_id(order_id):
        return (
            Order.objects.filter(id=order_id)
            .select_related("banding", "cutting")
            .prefetch_related("items__product")
            .first()
        )

    @staticmethod
    @transaction.atomic
    def checkout(
            user,
            payment_method,
            items,
            customer_id=None,
            covered_amount=0,
            discount=0,
            discount_type="c",
    ):
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

        customer = OrderService._get_customer(customer_id)
        source = Order.OrderSource.CASHIER if user.role == user.UserRoles.CASHIER else Order.OrderSource.SELLER

        order = Order.objects.create(
            user=user,
            source=source,
            customer=customer,
            is_anonymous=(customer is None),
            payment_method=payment_method,
            discount=discount,
            discount_type=discount_type,
            covered_amount=covered_amount,
        )

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CREATE,
            visible_for=(
                OrderHistory.VisibleFor.CASHIER
                if user.role == User.UserRoles.CASHIER
                else OrderHistory.VisibleFor.SELLER
            ),
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

        if payment_method != Order.PaymentMethod.NASIYA:
            order.covered_amount = order.total_price

        order.full_clean()
        order.save(update_fields=["total_price", "covered_amount"])

        remaining = order.total_price - order.covered_amount

        if order.customer:
            customer = Customer.objects.select_for_update().get(id=order.customer.id)

            if order.covered_amount > 0:
                BalanceHistory.objects.create(
                    customer=customer,
                    type=BalanceHistory.Type.ORDER_PAYMENT,
                    amount=order.covered_amount,
                )

            if order.payment_method == Order.PaymentMethod.NASIYA and remaining > 0:
                Customer.objects.filter(id=customer.id).update(debt=F("debt") + remaining)
                BalanceHistory.objects.create(
                    customer=customer,
                    type=BalanceHistory.Type.DEBT_ADD,
                    amount=remaining,
                )

        if not basket.items.exists():
            basket.is_active = False
            basket.save(update_fields=["is_active"])

        return (
            Order.objects.select_related("customer", "banding", "cutting")
            .prefetch_related("items__product")
            .get(id=order.id)
        )

    @staticmethod
    @transaction.atomic
    def create_cutting(data):
        customer = OrderService._get_customer(data.get("customer_id"))
        cutting = Cutting.objects.create(
            count=data["count"],
            price=data["price"],
            customer=customer,
            discount=data.get("discount", 0),
            discount_type=data.get("discount_type", Cutting.DiscountType.CASH),
            payment_method=data.get("payment_method", Cutting.PaymentMethod.CASH),
            covered_amount=data.get("covered_amount", 0),
        )
        OrderService._apply_customer_balance(cutting)
        return Cutting.objects.select_related("customer").get(id=cutting.id)

    @staticmethod
    @transaction.atomic
    def create_banding(data):
        customer = OrderService._get_customer(data.get("customer_id"))
        banding = Banding.objects.create(
            thickness=data.get("thickness"),
            length=data["length"],
            customer=customer,
            discount=data.get("discount", 0),
            discount_type=data.get("discount_type", Banding.DiscountType.CASH),
            payment_method=data.get("payment_method", Banding.PaymentMethod.CASH),
            covered_amount=data.get("covered_amount", 0),
        )
        OrderService._apply_customer_balance(banding)
        return Banding.objects.select_related("customer", "thickness").get(id=banding.id)
