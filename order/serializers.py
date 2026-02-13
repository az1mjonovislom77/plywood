from rest_framework import serializers
from order.models import Basket
from product.serializers import ProductSerializer


class BasketSerializers(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Basket
        fields = ['id', 'product']
