from rest_framework import serializers
from order.models import Basket, Cutting, BasketItem, Banding, Thickness
from product.models import Product
from product.serializers import ProductSerializer
from utils.base.serializers_base import BaseReadSerializer


class BasketItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = BasketItem
        fields = ["id", "product"]


class BasketSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, read_only=True)

    class Meta:
        model = Basket
        fields = ["id", "items"]


class BasketAddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product does not exist")

        return value


class CuttingSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Cutting


class ThicknessSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Thickness


class BandingGetSerializer(serializers.ModelSerializer):
    thickness = ThicknessSerializer(many=True, read_only=True)

    class Meta:
        model = Banding
        fields = ["id", "thickness", "width", "height"]


class BandingPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banding
        fields = ["id", "thickness", "width", "height"]
