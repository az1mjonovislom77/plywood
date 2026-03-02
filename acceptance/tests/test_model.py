from decimal import Decimal
from django.test import TestCase
from datetime import date
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from acceptance.models import CurrencyRate


class CurrencyRateModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_rate = CurrencyRate.objects.create(
            date=date(2024, 1, 1),
            rate=Decimal("10000.00")
        )

    def test_currency_rate_creations(self):
        rate = CurrencyRate.objects.create(
            date=date(2024, 2, 1),
            rate=Decimal("12345.67")
        )

        self.assertEqual(rate.date, date(2024, 1, 1))
        self.assertEqual(rate.rate, Decimal("12345.67"))

    def test_str_representation(self):
        self.assertEqual(str(self.existing_rate), "2024-01-01 - 10000.00")

    def test_date_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            CurrencyRate.objects.create(
                date=date(2024, 1, 1),
                rate=Decimal("9999.99")
            )

    def test_rate_max_digits_validation(self):
        rate = CurrencyRate(
            date=date(2024, 2, 1),
            rate=Decimal("1234566666666666666.67")
        )

        with self.assertRaises(ValidationError):
            rate.full_clean()

    def test_rate_decimal_places_validation(self):
        rate = CurrencyRate(
            date=date(2024, 4, 1),
            rate=Decimal("12345.6789")
        )

        with self.assertRaises(ValidationError):
            rate.full_clean()
