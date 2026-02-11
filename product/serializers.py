from rest_framework import serializers
from product.models import Product
from utils.base.serializers_base import BaseReadSerializer


class ManagerProductSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        exclude = ["arrival_price"]
