from category.models import Category
from utils.base.serializers_base import BaseReadSerializer


class CategorySerializer(BaseReadSerializer):
    class Meta(BaseReadSerializer.Meta):
        model = Category
