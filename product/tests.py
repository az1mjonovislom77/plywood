from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from unittest.mock import MagicMock
from product.api.serializers import ProductSerializer
from product.models import Product
from product.utils import check_image_size, check_image_content


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
