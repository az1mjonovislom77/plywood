from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from order.api.serializers import BasketAddItemSerializer, BasketSerializer
from order.service.basket import BasketService


@extend_schema(tags=["Basket"])
class BasketViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return BasketAddItemSerializer
        return BasketSerializer

    def list(self, request):
        basket = BasketService.get_basket(user=request.user)
        serializer = BasketSerializer(basket)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        basket = BasketService.add_product(user=request.user, product_id=serializer.validated_data["product_id"])
        return Response(BasketSerializer(basket).data)

    def destroy(self, request, pk=None):
        product_id = request.query_params.get("product_id", None)
        if not product_id:
            raise ValidationError({"product_id": "product_id required"})

        basket = BasketService.remove_product(user=request.user, product_id=product_id)
        return Response(BasketSerializer(basket).data)
