from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from order.models import Cutting, Banding, Thickness
from order.serializers import CuttingSerializer, BasketSerializer, BasketAddItemSerializer, \
    ThicknessSerializer, BandingGetSerializer, BandingPostSerializer, OrderCreateSerializer, OrderSerializer
from order.service.basket import BasketService
from order.service.order import OrderService
from utils.base.views_base import BaseUserViewSet
from django.utils.dateparse import parse_date


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
        basket = BasketService.remove_product(user=request.user, product_id=product_id)

        return Response(BasketSerializer(basket).data)


@extend_schema(tags=["Cutting"])
class CuttingViewSet(BaseUserViewSet):
    queryset = Cutting.objects.all()
    serializer_class = CuttingSerializer

    ordering = ["-created_at"]

    def get_queryset(self):
        date_param = self.request.query_params.get("date") or timezone.localdate()
        return self.queryset.filter(created_at__date=date_param)


@extend_schema(tags=["Banding"])
class BandingViewSet(BaseUserViewSet):
    queryset = Banding.objects.select_related("thickness").all()

    ordering = ["-created_at"]

    def get_queryset(self):
        date_param = self.request.query_params.get("date") or timezone.localdate()
        return self.queryset.filter(created_at__date=date_param)

    def get_serializer_class(self):
        if self.action == "create":
            return BandingPostSerializer
        return BandingGetSerializer


@extend_schema(tags=["Thickness"])
class ThicknessViewSet(BaseUserViewSet):
    queryset = Thickness.objects.all()
    serializer_class = ThicknessSerializer

    ordering = ["-id"]


@extend_schema(tags=["Order"])
class OrderViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None

    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        queryset = OrderService.get_all(user=self.request.user)

        date_param = self.request.query_params.get("date")
        parsed_date = parse_date(date_param) if date_param else timezone.localdate()

        return queryset.filter(created_at__date=parsed_date)

    def list(self, request):
        serializer = OrderSerializer(self.get_queryset(), many=True)

        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        order = OrderService.get_by_id(user=request.user, order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderService.checkout(
            user=request.user,
            payment_method=serializer.validated_data["payment_method"],
            items=serializer.validated_data["items"],
            customer_id=serializer.validated_data.get("customer_id"),
            discount=serializer.validated_data.get("discount"),
            discount_type=serializer.validated_data.get("discount_type"),
            covered_amount=serializer.validated_data.get("covered_amount"),
            banding_data=serializer.validated_data.get("banding"),
            cutting_data=serializer.validated_data.get("cutting"))

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        order = OrderService.get_by_id(user=request.user, order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        order = OrderService.get_by_id(user=request.user, order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        order.delete()

        return Response({"detail": "Order deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
