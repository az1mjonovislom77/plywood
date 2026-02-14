from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from order.models import Cutting, Banding, Thickness
from order.serializers import CuttingSerializer, BasketSerializer, BasketAddItemSerializer, \
    ThicknessSerializer, BandingGetSerializer, BandingPostSerializer
from order.service.basket import BasketService
from utils.base.views_base import BaseUserViewSet


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
        serializer = BasketSerializer(basket, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = BasketAddItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        basket = BasketService.add_product(user=request.user, product_id=serializer.validated_data["product_id"])
        response_serializer = BasketSerializer(basket, context={"request": request})

        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request):
        product_id = request.data.get("product_id")
        basket = BasketService.remove_product(user=request.user, product_id=product_id)
        serializer = BasketSerializer(basket, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=["Cutting"])
class CuttingViewSet(BaseUserViewSet):
    queryset = Cutting.objects.all()
    serializer_class = CuttingSerializer

    ordering = ["-id"]


@extend_schema(tags=["Banding"])
class BandingViewSet(BaseUserViewSet):
    queryset = Banding.objects.select_related("thickness")

    ordering = ["-id"]

    def get_serializer_class(self):
        if self.action == "create":
            return BandingPostSerializer
        return BandingGetSerializer


@extend_schema(tags=["Thickness"])
class ThicknessViewSet(BaseUserViewSet):
    queryset = Thickness.objects.all()
    serializer_class = ThicknessSerializer

    ordering = ["-id"]
