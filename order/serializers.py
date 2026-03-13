from rest_framework import serializers
from order.models import Basket, Cutting, BasketItem, Banding, Thickness, Order, OrderItem, OrderHistory
from product.models import Product
from product.serializers import ProductSerializer
from user.models import User
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
        fields = ["id", "count", "price", "total_price", "created_at"]

    def get_total_price(self, obj):
        return obj.calculate_price()


class ThicknessSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Thickness


class BandingGetSerializer(serializers.ModelSerializer):
    thickness = ThicknessSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Banding

        fields = ["id", "thickness", "length", "total_price", "created_at"]

    def get_total_price(self, obj):
        return obj.calculate_price()


class BandingPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banding
        fields = ["id", "thickness", "length"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "price", "quantity"]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "quantity"]

    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("Product not found")
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
    customer_fullname = serializers.SerializerMethodField()
    history = serializers.SerializerMethodField()
    accepted_by_name = serializers.CharField(source="accepted_by.full_name", read_only=True)
    accepted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order

        fields = ["id", "user", "customer_fullname", "is_anonymous", "discount_type", "discount", "payment_method",
                  "covered_amount", "banding", "cutting", "total_price", "items", "source", "order_status",
                  "accepted_by_name", "accepted_at", "history", "created_at"]

        read_only_fields = ["source", "order_status"]

    def get_customer_fullname(self, obj):
        return obj.customer.full_name if obj.customer else None

    def get_history(self, obj):
        request = self.context.get("request")
        if not request:
            return []

        user = request.user

        if user.role == User.UserRoles.MANAGER or User.UserRoles.SELLER or User.UserRoles.CASHIER or User.UserRoles.WAREHOUSEMAN:
            queryset = obj.history.all()
        # elif user.role == User.UserRoles.SELLER:
        #     queryset = obj.history.filter(visible_for=OrderHistory.VisibleFor.SELLER)
        # elif user.role == User.UserRoles.CASHIER:
        #     queryset = obj.history.filter(visible_for=OrderHistory.VisibleFor.CASHIER)
        else:
            queryset = obj.history.none()

        return OrderHistorySerializer(queryset, many=True, context=self.context).data


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)
    customer_id = serializers.IntegerField(required=False)
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    discount_type = serializers.ChoiceField(choices=Order.DiscountType.choices, default=Order.DiscountType.CASH)
    covered_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)
    banding = BandingPostSerializer(required=False)
    cutting = CuttingSerializer(required=False)


class OrderCancelSerializer(serializers.Serializer):
    description = serializers.CharField(required=False, allow_blank=True)
