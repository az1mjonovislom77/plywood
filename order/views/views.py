from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from order.models import Cutting, Banding, Thickness, OrderHistory
from order.serializers import CuttingSerializer, BasketSerializer, BasketAddItemSerializer, \
    ThicknessSerializer, BandingGetSerializer, BandingPostSerializer, OrderCreateSerializer, OrderSerializer, \
    OrderHistorySerializer, OrderCancelSerializer
from order.service.basket import BasketService
from order.service.order import OrderService
from order.service.order_query import OrderQueryService
from utils.base.views_base import BaseUserViewSet
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from order.service.order_workflow import OrderWorkflowService
from user.models import User


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
        queryset = OrderQueryService.list_for_user(self.request.user)

        date_param = self.request.query_params.get("date")

        if date_param:
            parsed_date = parse_date(date_param)
            if not parsed_date:
                raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD"})
        else:
            parsed_date = timezone.localdate()

        return queryset.filter(created_at__date=parsed_date)

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        order = self.get_queryset().filter(id=pk).first()

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(order, context={"request": request})
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
            cutting_data=serializer.validated_data.get("cutting"),
        )

        response = OrderSerializer(order, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        order = OrderService.get_by_id(order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND, )

        serializer = OrderSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        order = OrderService.get_by_id(order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND, )

        order.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):

        if request.user.role != User.UserRoles.CASHIER:
            return Response({"detail": "Only cashier can accept orders"}, status=status.HTTP_403_FORBIDDEN)
        try:
            order = OrderWorkflowService.cashier_accept(order_id=pk, user=request.user)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)

    @extend_schema(request=OrderCancelSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        description = request.data.get("description")

        try:
            if request.user.role == User.UserRoles.SELLER:
                order = OrderWorkflowService.seller_cancel(pk, request.user, description)
            else:
                order = OrderWorkflowService.cashier_cancel(pk, request.user, description)

        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["OrderHistory"])
class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderHistorySerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user

        queryset = OrderHistory.objects.select_related("user", "order")

        if user:
            return queryset

        return queryset.none()
