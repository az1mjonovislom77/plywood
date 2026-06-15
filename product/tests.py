from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import MagicMock
from product.api.serializers import ProductSerializer
from product.models import Product
from product.selectors import ProductSelector
from product.utils import check_image_size, check_image_content
from category.models import Category


class ProductSerializerTest(TestCase):
    def test_count_trims_trailing_zeroes(self):
        product = Product.objects.create(name="Plywood", count=Decimal("25.000"))

        data = ProductSerializer(product).data

        self.assertEqual(data["count"], "25")


class ImageSizeValidatorTest(TestCase):
    def test_rejects_oversized_image(self):
        mock_image = MagicMock()
        mock_image.size = 11 * 1024 * 1024
        with self.assertRaises(ValidationError):
            check_image_size(mock_image)

    def test_accepts_image_within_limit(self):
        mock_image = MagicMock()
        mock_image.size = 5 * 1024 * 1024
        check_image_size(mock_image)

    def test_rejects_exactly_over_limit(self):
        mock_image = MagicMock()
        mock_image.size = 10 * 1024 * 1024 + 1
        with self.assertRaises(ValidationError):
            check_image_size(mock_image)


class ImageContentValidatorTest(TestCase):
    def test_skips_validation_for_svg(self):
        mock_image = MagicMock()
        mock_image.name = "icon.svg"
        check_image_content(mock_image)

    def test_skips_validation_for_uppercase_svg(self):
        mock_image = MagicMock()
        mock_image.name = "icon.SVG"
        check_image_content(mock_image)

    def test_rejects_non_image_file_with_image_extension(self):
        import io
        buf = io.BytesIO(b"this is definitely not a real image file content")
        buf.name = "fake.png"
        with self.assertRaises(ValidationError):
            check_image_content(buf)


class ProductSelectorTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Test Category")
        self.active1 = Product.objects.create(name="Active 1", is_active=True, category=self.category)
        self.active2 = Product.objects.create(name="Active 2", is_active=True, category=self.category)
        self.inactive = Product.objects.create(name="Inactive", is_active=False, category=self.category)
        self.other_category = Category.objects.create(name="Other Category")
        self.other = Product.objects.create(name="Other Cat", is_active=True, category=self.other_category)

    def test_active_products_returns_only_active(self):
        qs = ProductSelector.active_products()
        ids = list(qs.values_list("id", flat=True))
        self.assertIn(self.active1.id, ids)
        self.assertIn(self.active2.id, ids)
        self.assertNotIn(self.inactive.id, ids)

    def test_inactive_products_returns_only_inactive(self):
        qs = ProductSelector.inactive_products()
        ids = list(qs.values_list("id", flat=True))
        self.assertIn(self.inactive.id, ids)
        self.assertNotIn(self.active1.id, ids)

    def test_products_by_category_filters_correctly(self):
        qs = ProductSelector.products_by_category(self.category.id)
        ids = list(qs.values_list("id", flat=True))
        self.assertIn(self.active1.id, ids)
        self.assertIn(self.active2.id, ids)
        self.assertNotIn(self.inactive.id, ids)
        self.assertNotIn(self.other.id, ids)

    def test_product_by_id_returns_correct_active_product(self):
        result = ProductSelector.product_by_id(self.active1.id)
        self.assertEqual(result, self.active1)

    def test_product_by_id_returns_none_for_inactive(self):
        result = ProductSelector.product_by_id(self.inactive.id)
        self.assertIsNone(result)
