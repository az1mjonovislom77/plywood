from product.models import Product
from utils.base.serializers_base import BaseReadSerializer


class ProductSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Product
