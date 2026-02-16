from rest_framework import serializers
from order.models import Basket, Cutting, BasketItem, Banding, Thickness, Order, OrderItem
from product.models import Product
from product.serializers import ProductSerializer
from utils.base.serializers_base import BaseReadSerializer


class BasketItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

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


class CuttingSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cutting
        fields = ["count", "price", "total_price"]

    def get_total_price(self, obj):
        return obj.calculate_price()


class ThicknessSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Thickness


class BandingGetSerializer(serializers.ModelSerializer):
    thickness = ThicknessSerializer(read_only=True)
    linear_meter = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Banding

        fields = ["id", "thickness", "width", "height", "linear_meter", "total_price"]

    def get_linear_meter(self, obj):
        return obj.linear_meter()

    def get_total_price(self, obj):
        return obj.calculate_price()


class BandingPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banding
        fields = ["id", "thickness", "width", "height"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "price", "quantity"]

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
        return value


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ["product_id", "quantity"]

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    banding = BandingGetSerializer(read_only=True)
    cutting = CuttingSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order

        fields = ["id", "user", "discount_type", "discount", "payment_method", "covered_amount", "banding",
                  "cutting", "total_price", "items", "created_at"]


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)
    customer_id = serializers.IntegerField(required=False)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    discount_type = serializers.ChoiceField(choices=Order.DiscountType.choices, default=Order.DiscountType.CASH)
    covered_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    banding = BandingPostSerializer(required=False)
    cutting = CuttingSerializer(required=False)
