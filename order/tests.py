from django.test import TestCase
from rest_framework.test import APIRequestFactory
from order.api.serializers import OrderSerializer
from order.models import Order, OrderHistory
from user.models import User


class OrderSerializerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.seller = User.objects.create_user(username="seller", password="123", role=User.UserRoles.SELLER)
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
