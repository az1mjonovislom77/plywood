from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from order.models import Basket
from order.serializers import BasketSerializers


@extend_schema(tags=["Basket"])
class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.select_related("product")
    serializer_class = BasketSerializers
    http_method_names = ["get", "post", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    ordering = ["-id"]
