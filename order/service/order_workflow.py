from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from customer.models import Customer
from order.models import Order
from product.models import Product
from user.models import User
from order.models import OrderHistory, OrderItem
from acceptance.models import CurrencyRate
from order.service.order import OrderService


class OrderWorkflowService:

    @staticmethod
    @transaction.atomic
    def seller_cancel(order_id, user, description=None):

        if user.role != User.UserRoles.SELLER:
            raise ValueError("Only seller can cancel")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.user_id != user.id:
            raise ValueError("Not your order")

        if order.source != Order.OrderSource.SELLER:
            raise ValueError("Seller cannot cancel cashier order")

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already closed")

        order.order_status = Order.OrderStatus.CANCEL
        order.save(update_fields=["order_status"])

        if order.customer:
            order.customer.sync_debt()

        for item in order.items.select_related("product"):
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CANCEL,
            visible_for=OrderHistory.VisibleFor.SELLER,
            description=description
        )

        return order

    @staticmethod
    @transaction.atomic
    def cashier_accept(order_id, user):

        if user.role != User.UserRoles.CASHIER:
            raise ValueError("Only cashier can accept")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already processed")

        order.order_status = Order.OrderStatus.ACCEPT
        order.accepted_by = user
        order.accepted_at = timezone.now()

        order.save(update_fields=[
            "order_status",
            "accepted_by",
            "accepted_at"
        ])

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.ACCEPT,
            visible_for=OrderHistory.VisibleFor.CASHIER
        )

        return order

    @staticmethod
    @transaction.atomic
    def cashier_cancel(order_id, user, description=None):

        if user.role != User.UserRoles.CASHIER:
            raise ValueError("Only cashier can cancel")

        order = Order.objects.select_for_update().get(id=order_id)

        if order.order_status != Order.OrderStatus.WAITING:
            raise ValueError("Order already processed")

        order.order_status = Order.OrderStatus.CANCEL
        order.save(update_fields=["order_status"])

        if order.customer:
            order.customer.sync_debt()

        for item in order.items.select_related("product"):
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.CANCEL,
            visible_for=OrderHistory.VisibleFor.CASHIER,
            description=description
        )
        return order

    @staticmethod
    @transaction.atomic
    def update_order(order_id, user, data):
        order = Order.objects.select_for_update().get(id=order_id)

        if order.order_status == Order.OrderStatus.CANCEL:
            raise ValueError("Bekor qilingan buyurtmani o'zgartirib bo'lmaydi")

        is_accepted_order = order.order_status == Order.OrderStatus.ACCEPT
        description = data.get('description', '')
        if is_accepted_order:
            accepted_by_user = order.accepted_by.username if order.accepted_by else 'N/A'
            accepted_info = f"[Tasdiqlangan buyurtma tahrirlandi (Accepted by: {accepted_by_user})] "
            description = accepted_info + description

        if user.role == User.UserRoles.SELLER and order.user_id != user.id:
            raise ValueError("Siz faqat o'zingizni buyurtmangizni o'zgartira olasiz")
        elif user.role not in [User.UserRoles.SELLER, User.UserRoles.CASHIER, User.UserRoles.MANAGER]:
            raise ValueError("Sizda bu operatsiyaga ruxsat yo'q")

        today = timezone.localdate()
        rate_obj = CurrencyRate.objects.filter(date=today).first()
        if not rate_obj:
            raise ValueError("Bugungi dollar kursi kiritilmagan")
        rate_value = rate_obj.rate

        current_items = {item.id: item for item in order.items.all()}
        incoming_items_map = {item.get('id'): item for item in data['items'] if item.get('id')}
        new_items_data = [item for item in data['items'] if not item.get('id')]

        item_ids_to_delete = set(current_items.keys()) - set(incoming_items_map.keys())
        for item_id in item_ids_to_delete:
            item = current_items[item_id]
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)
            item.delete()

        for item_id, item_data in incoming_items_map.items():
            item = current_items[item_id]
            quantity_diff = Decimal(item_data['quantity']) - item.quantity

            if quantity_diff != 0:
                if quantity_diff > 0 and item.product.count < quantity_diff:
                    raise ValueError(f"{item.product.name} yetarli miqdorda mavjud emas")
                Product.objects.filter(id=item.product_id).update(count=F("count") - quantity_diff)

            original_sell_price = item.product.sale_price
            new_sell_price = item_data.get("new_sell_price")
            actual_sell_price = new_sell_price if new_sell_price is not None else item.price
            sell_price_difference = actual_sell_price - original_sell_price if new_sell_price is not None else item.sell_price_difference

            price_in_dollar = item.price_in_dollar
            new_price_in_dollar = item.new_price_in_dollar
            if rate_value is not None and rate_value != Decimal("0"):
                if new_sell_price is not None:
                    new_price_in_dollar = (new_sell_price / rate_value).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )

            item.quantity = Decimal(item_data['quantity'])
            item.price = actual_sell_price
            item.new_sell_price = new_sell_price
            item.sell_price_difference = sell_price_difference
            item.new_price_in_dollar = new_price_in_dollar
            item.save()

        new_order_items = []
        for item_data in new_items_data:
            product = Product.objects.get(id=item_data['product_id'])
            quantity = Decimal(item_data['quantity'])

            if product.count < quantity:
                raise ValueError(f"{product.name} yetarli miqdorda mavjud emas")

            Product.objects.filter(id=product.id).update(count=F("count") - quantity)

            original_sell_price = product.sale_price
            new_sell_price = item_data.get("new_sell_price")
            actual_sell_price = new_sell_price if new_sell_price is not None else original_sell_price
            sell_price_difference = actual_sell_price - original_sell_price if new_sell_price is not None else 0

            price_in_dollar = None
            new_price_in_dollar = None
            if rate_value is not None and rate_value != Decimal("0"):
                price_in_dollar = (original_sell_price / rate_value).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
                if new_sell_price is not None:
                    new_price_in_dollar = (new_sell_price / rate_value).quantize(
                        Decimal("0.0001"), rounding=ROUND_HALF_UP
                    )

            new_order_items.append(OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price=actual_sell_price,
                original_sell_price=original_sell_price,
                new_sell_price=new_sell_price,
                sell_price_difference=sell_price_difference,
                exchange_rate=rate_value,
                price_in_dollar=price_in_dollar,
                new_price_in_dollar=new_price_in_dollar,
            ))

        if new_order_items:
            OrderItem.objects.bulk_create(new_order_items)

        old_customer = order.customer
        new_customer = OrderService._get_customer(data.get("customer_id"))
        
        order.customer = new_customer
        order.is_anonymous = (new_customer is None)
        order.payment_method = data['payment_method']
        order.discount = Decimal(data.get('discount', 0))
        order.discount_type = data.get('discount_type', Order.DiscountType.CASH)
        order.covered_amount = Decimal(data.get('covered_amount', 0))

        if order.payment_method != Order.PaymentMethod.NASIYA:
            order.calculate_total()
            order.covered_amount = order.total_price

        order.calculate_total()
        order.full_clean()
        order.save()

        if old_customer and old_customer != new_customer:
            old_customer.sync_debt()
        if new_customer:
            new_customer.sync_debt()

        OrderHistory.objects.create(
            order=order,
            user=user,
            action=OrderHistory.Action.UPDATE,
            visible_for=(OrderHistory.VisibleFor.CASHIER
                         if user.role == User.UserRoles.CASHIER
                         else OrderHistory.VisibleFor.SELLER),
            description=description
        )

        return order