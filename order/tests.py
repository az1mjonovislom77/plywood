from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from acceptance.models import CurrencyRate
from order.api.serializers import OrderSerializer
from order.models import Basket, BasketItem, Order, OrderHistory, OrderItem
from order.service.order import OrderService
from product.models import Product
from user.models import User
from customer.models import Customer


class OrderSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.seller = User.objects.create_user(username="seller", password="123", role=User.UserRoles.SELLER)
        CurrencyRate.objects.create(date=timezone.localdate(), rate=Decimal("12500.00"))
        self.order = Order.objects.create(user=self.seller, payment_method=Order.PaymentMethod.CASH)
        OrderHistory.objects.create(
            order=self.order,
            user=self.seller,
            action=OrderHistory.Action.CREATE,
            visible_for=OrderHistory.VisibleFor.SELLER,
        )

    def test_history_is_available_for_allowed_roles_only(self):
        request = self.factory.get("/orders/")
        request.user = self.seller

        data = OrderSerializer(self.order, context={"request": request}).data

        self.assertEqual(len(data["history"]), 1)

    def test_history_hidden_for_unknown_role(self):
        outsider = User.objects.create_user(username="outsider", password="123", role="x")
        request = self.factory.get("/orders/")
        request.user = outsider

        data = OrderSerializer(self.order, context={"request": request}).data

        self.assertEqual(data["history"], [])

    def test_order_item_includes_sell_price_fields(self):
        product = Product.objects.create(name="Plywood", sale_price=Decimal("400000.00"))
        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=Decimal("1"),
            price=Decimal("450000.00"),
            original_sell_price=Decimal("400000.00"),
            new_sell_price=Decimal("450000.00"),
            sell_price_difference=Decimal("50000.00"),
            exchange_rate=Decimal("12500.00"),
            price_in_dollar=Decimal("32.0000"),
            new_price_in_dollar=Decimal("36.0000"),
        )
        request = self.factory.get("/orders/")
        request.user = self.seller

        data = OrderSerializer(self.order, context={"request": request}).data

        self.assertNotIn("items", data["history"][0])

        item = data["items"][0]
        self.assertEqual(item["price"], "450000.00")
        self.assertEqual(item["original_sell_price"], "400000.00")
        self.assertEqual(item["new_sell_price"], "450000.00")
        self.assertEqual(item["sell_price_difference"], "50000.00")
        self.assertEqual(item["price_in_dollar"], "32.0000")
        self.assertEqual(item["new_price_in_dollar"], "36.0000")

    def test_checkout_uses_new_sell_price_when_provided(self):
        product = Product.objects.create(name="Plywood", sale_price=Decimal("400000.00"), count=Decimal("2.000"))
        basket = Basket.objects.create(user=self.seller)
        BasketItem.objects.create(basket=basket, product=product)

        order = OrderService.checkout(
            user=self.seller,
            payment_method=Order.PaymentMethod.CASH,
            items=[{
                "product_id": product.id,
                "quantity": Decimal("1.000"),
                "new_sell_price": Decimal("450000.00"),
            }],
        )

        item = order.items.get()
        self.assertEqual(item.price, Decimal("450000.00"))
        self.assertEqual(item.original_sell_price, Decimal("400000.00"))
        self.assertEqual(item.new_sell_price, Decimal("450000.00"))
        self.assertEqual(item.sell_price_difference, Decimal("50000.00"))
        self.assertEqual(item.price_in_dollar, Decimal("32.0000"))
        self.assertEqual(item.new_price_in_dollar, Decimal("36.0000"))
        self.assertEqual(order.total_price, Decimal("450000.00"))

    def test_checkout_creates_cutting_and_banding_for_each_product(self):
        product = Product.objects.create(name="Plywood", sale_price=Decimal("400000.00"), count=Decimal("2.000"))
        basket = Basket.objects.create(user=self.seller)
        BasketItem.objects.create(basket=basket, product=product)

        order = OrderService.checkout(
            user=self.seller,
            payment_method=Order.PaymentMethod.CASH,
            items=[{
                "product_id": product.id,
                "quantity": Decimal("1.000"),
                "cutting": {"count": Decimal("2.000"), "price": Decimal("15000.00")},
                "banding": {"thickness": Decimal("10000.00"), "length": Decimal("3.000")},
            }],
        )

        item = order.items.get()
        self.assertIsNotNone(item.cutting)
        self.assertIsNotNone(item.banding)
        self.assertEqual(order.total_price, Decimal("460000.00"))
        self.assertEqual(order.covered_amount, Decimal("460000.00"))

        request = self.factory.get("/orders/")
        request.user = self.seller
        data = OrderSerializer(order, context={"request": request}).data
        self.assertEqual(data["items"][0]["quantity"], "1")
        self.assertEqual(data["items"][0]["cutting"]["count"], "2")
        self.assertEqual(data["items"][0]["cutting"]["total_price"], Decimal("30000.00000"))
        self.assertEqual(data["items"][0]["banding"]["total_price"], Decimal("30000.0000"))

    def test_checkout_uses_customer_overpayment_before_adding_debt(self):
        customer = Customer.objects.create(full_name="Credit Customer", overpayment=Decimal("50.00"))
        product = Product.objects.create(name="Plywood", sale_price=Decimal("120.00"), count=Decimal("2.000"))
        basket = Basket.objects.create(user=self.seller)
        BasketItem.objects.create(basket=basket, product=product)

        OrderService.checkout(
            user=self.seller,
            payment_method=Order.PaymentMethod.NASIYA,
            customer_id=customer.id,
            covered_amount=Decimal("0.00"),
            items=[{
                "product_id": product.id,
                "quantity": Decimal("1.000"),
            }],
        )

        customer.refresh_from_db()

        self.assertEqual(customer.overpayment, Decimal("0.00"))
        self.assertEqual(customer.debt, Decimal("70.00"))
