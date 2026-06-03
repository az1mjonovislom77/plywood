from decimal import Decimal
from django.test import TestCase
from product.api.serializers import ProductSerializer
from product.models import Product


class ProductSerializerTest(TestCase):
    def test_count_trims_trailing_zeroes(self):
        product = Product.objects.create(name="Plywood", count=Decimal("25.000"))

        data = ProductSerializer(product).data

        self.assertEqual(data["count"], "25")
