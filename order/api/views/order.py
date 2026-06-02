from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from order.api.serializers import OrderCancelSerializer, OrderCreateSerializer, OrderSerializer, OrderUpdateSerializer
from order.models import Order
from order.service.order import OrderService
from order.service.order_export import generate_order_ledger_excel
from order.service.order_query import OrderQueryService
from order.service.order_workflow import OrderWorkflowService
from user.models import User


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)
        total_pages = (total + limit - 1) // limit

        return Response(
            {
                "page": self.page.number,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "data": data,
            }
        )


@extend_schema(tags=["Order"])
class OrderViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = OrderPagination
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        if self.action == "update":
            return OrderUpdateSerializer
        return OrderSerializer

    def get_queryset(self):
        return OrderQueryService.list_for_user(self.request.user).order_by("-created_at")

    def _get_list_queryset(self, request):
        queryset = self.get_queryset()

        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        customer_id = request.query_params.get("customer_id")

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        if date_from:
            parsed_from = parse_date(date_from)
            if not parsed_from:
                raise ValidationError({"from": "Invalid date format. Use YYYY-MM-DD"})
        else:
            parsed_from = timezone.localdate()

        if date_to:
            parsed_to = parse_date(date_to)
            if not parsed_to:
                raise ValidationError({"to": "Invalid date format. Use YYYY-MM-DD"})
        else:
            parsed_to = parsed_from

        start = timezone.make_aware(timezone.datetime.combine(parsed_from, timezone.datetime.min.time()))
        end = timezone.make_aware(timezone.datetime.combine(parsed_to, timezone.datetime.max.time()))

        return queryset.filter(created_at__gte=start, created_at__lte=end)

    @extend_schema(parameters=[
        OpenApiParameter(name="from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="customer_id", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY)]
    )
    def list(self, request):
        queryset = self._get_list_queryset(request)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)

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
        )

        response = OrderSerializer(order, context={"request": request})
        return Response(response.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            order = OrderWorkflowService.update_order(
                order_id=pk,
                user=request.user,
                data=serializer.validated_data
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

        response = OrderSerializer(order, context={"request": request})
        return Response(response.data)

    def destroy(self, request, pk=None):
        order = OrderService.get_by_id(order_id=pk)

        if not order:
            return Response({"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

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


@extend_schema(tags=["OrderExport"])
class OrderExcelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        order = get_object_or_404(Order.objects.select_related("customer").prefetch_related("items__product"), pk=pk)

        file = generate_order_ledger_excel(order)

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="order_{order.id}.xlsx"'
            },
        )