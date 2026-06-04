from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from acceptance.models import CurrencyRate
from category.models import Category
from order.models import Banding, Order, OrderItem
from product.api.serializers import ProductSerializer
from product.models import Product
from product.services.ancillary_profit import AncillaryProfitService
from product.services.material_profit import MaterialProfitService


class ProductSerializerTest(TestCase):
    def test_count_trims_trailing_zeroes(self):
        product = Product.objects.create(name="Plywood", count=Decimal("25.000"))

        data = ProductSerializer(product).data

        self.assertEqual(data["count"], "25")


class BandingProfitTest(TestCase):
    def setUp(self):
        today = timezone.localdate()
        CurrencyRate.objects.create(date=today, rate=Decimal("12500.00"))
        self.kromka = Category.objects.create(name="KROMKA")
        self.product = Product.objects.create(
            name="Kromka roll",
            category=self.kromka,
            sale_price=Decimal("100000.00"),
            count=Decimal("10.000"),
        )
        self.order = Order.objects.create(
            order_status=Order.OrderStatus.ACCEPT,
            payment_method=Order.PaymentMethod.NASIYA,
            covered_amount=Decimal("0"),
            accepted_at=timezone.now(),
        )
        self.banding = Banding.objects.create(
            thickness=Decimal("100000.00"),
            length=Decimal("5.00"),
            payment_method=Banding.PaymentMethod.NASIYA,
            covered_amount=Decimal("0"),
        )
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=Decimal("1"),
            price=Decimal("0"),
            banding=self.banding,
        )

    def test_banding_profit_counts_service_amount_not_payment(self):
        today = timezone.localdate()
        context = MaterialProfitService.build_profit_context(
            str(today), str(today)
        )
        banding_som, _ = AncillaryProfitService.calc_banding_profit(
            context["start_dt"],
            context["end_dt"],
            context["rate_value"],
        )
        expected = Decimal("500000.00")
        self.assertEqual(banding_som, expected)

    def test_kromka_total_includes_product_and_banding(self):
        today = timezone.localdate()
        context = MaterialProfitService.build_profit_context(
            str(today), str(today)
        )
        product_som, _, _ = MaterialProfitService.calc_kromka_product_profit(context)
        banding_som, _ = AncillaryProfitService.calc_banding_profit(
            context["start_dt"],
            context["end_dt"],
            context["rate_value"],
        )
        self.assertEqual(banding_som, Decimal("500000.00"))
        self.assertGreaterEqual(product_som + banding_som, Decimal("500000.00"))
