from rest_framework import serializers
from order.models import Basket, Cutting, BasketItem, Banding, Thickness, Order, OrderItem, OrderHistory
from product.models import Product
from product.api.serializers import ProductSerializer
from user.models import User
from utils.base.serializers_base import BaseReadSerializer, TrimmedDecimalField


def get_service_total(obj):
    total = obj.calculate_price()

    if obj.discount > 0:
        if obj.discount_type == obj.DiscountType.PERCENTAGE:
            total -= total * (obj.discount / 100)
        else:
            total -= obj.discount

    return max(total, 0)


def validate_percentage_discount(discount_type, discount):
    if discount_type == "p" and discount > 100:
        raise serializers.ValidationError({"discount": "Foiz chegirma 100 dan katta bo'lib ketti"})


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
    customer_fullname = serializers.CharField(source="customer.full_name", read_only=True)
    count = TrimmedDecimalField(max_digits=20, decimal_places=3, read_only=True)

    class Meta:
        model = Cutting
        fields = [
            "id", "count", "price", "customer", "customer_fullname", "discount_type", "discount",
            "payment_method", "covered_amount", "total_price", "created_at"
        ]

    def get_total_price(self, obj):
        return get_service_total(obj)


class ThicknessSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Thickness


class BandingGetSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    customer_fullname = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = Banding
        fields = [
            "id", "thickness", "length", "customer", "customer_fullname", "discount_type", "discount",
            "payment_method", "covered_amount", "total_price", "created_at"
        ]

    def get_total_price(self, obj):
        return get_service_total(obj)


class BandingPostSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(required=False)

    class Meta:
        model = Banding
        fields = ["id", "thickness", "length", "customer_id", "discount_type", "discount", "payment_method",
                  "covered_amount"]

    def validate(self, attrs):
        validate_percentage_discount(
            attrs.get("discount_type", Banding.DiscountType.CASH),
            attrs.get("discount", 0))
        return attrs


class CuttingCreateSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(required=False)

    class Meta:
        model = Cutting
        fields = ["id", "count", "price", "customer_id", "discount_type", "discount", "payment_method",
                  "covered_amount"]

    def validate(self, attrs):
        validate_percentage_discount(
            attrs.get("discount_type", Cutting.DiscountType.CASH),
            attrs.get("discount", 0))
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    banding = BandingGetSerializer(read_only=True)
    cutting = CuttingSerializer(read_only=True)
    quantity = TrimmedDecimalField(max_digits=20, decimal_places=3, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            "id", "product", "banding", "cutting", "price", "quantity", "original_sell_price", "new_sell_price",
            "sell_price_difference", "exchange_rate", "price_in_dollar", "new_price_in_dollar",
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()
    new_sell_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    cutting = CuttingCreateSerializer(required=False)
    banding = BandingPostSerializer(required=False)

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "quantity", "new_sell_price", "cutting", "banding"]

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
        return value

    def validate_new_sell_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("New sell price must be greater than 0")
        return value


class OrderHistorySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = OrderHistory
        fields = ["id", "user", "user_name", "action", "visible_for", "description", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    banding = BandingGetSerializer(read_only=True)
    cutting = CuttingSerializer(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    customer_fullname = serializers.CharField(source="customer.full_name", read_only=True)
    history = serializers.SerializerMethodField()
    accepted_by_name = serializers.CharField(source="accepted_by.full_name", read_only=True)
    accepted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order

        fields = ["id", "user", "customer", "customer_fullname", "is_anonymous", "discount_type", "discount",
                  "payment_method", "covered_amount", "banding", "cutting", "total_price", "items", "source",
                  "order_status", "accepted_by_name", "accepted_at", "history", "created_at"]

        read_only_fields = ["source", "order_status"]

    def to_representation(self, instance):

        try:
            return super().to_representation(instance)

        except Exception as e:

            print("BROKEN ORDER:", instance.id)
            print("TOTAL:", instance.total_price)
            print("COVERED:", instance.covered_amount)
            print("DISCOUNT:", instance.discount)

            for item in instance.items.all():
                print("ITEM:", item.id)
                print("QTY:", item.quantity)
                print("PRICE:", item.price)
                print("ORIGINAL:", item.original_sell_price)
                print("NEW:", item.new_sell_price)
                print("DIFF:", item.sell_price_difference)
                print("RATE:", item.exchange_rate)
                print("USD:", item.price_in_dollar)
                print("NEW USD:", item.new_price_in_dollar)

            raise e

    def get_history(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        user = request.user
        if user.role not in [
            User.UserRoles.MANAGER,
            User.UserRoles.SELLER,
            User.UserRoles.CASHIER,
            User.UserRoles.WAREHOUSEMAN,
        ]:
            return []

        return OrderHistorySerializer(obj.history.all(), many=True, context=self.context).data


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)
    customer_id = serializers.IntegerField(required=False)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    discount = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, default=0)
    discount_type = serializers.ChoiceField(choices=Order.DiscountType.choices, default=Order.DiscountType.CASH)
    covered_amount = serializers.DecimalField(max_digits=20, decimal_places=2, required=False, default=0)

    def validate(self, attrs):
        validate_percentage_discount(
            attrs.get("discount_type", Order.DiscountType.CASH),
            attrs.get("discount", 0),
        )
        return attrs


class OrderCancelSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)
