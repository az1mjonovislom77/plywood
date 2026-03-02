from django.test import TestCase
from category.models import Category


class CategoryModelTest(TestCase):

    def test_str_representation(self):
        category = Category.objects.create(name="Electronics")
        self.assertEqual(str(category), "Electronics")
