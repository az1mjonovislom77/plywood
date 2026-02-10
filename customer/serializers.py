from customer.models import Customer
from utils.base.serializers_base import BaseReadSerializer


class CustomerSerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Customer
