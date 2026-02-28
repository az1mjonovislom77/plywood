from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status, filters
from utils.base.views_base import BaseUserViewSet
from .models import Supplier
from .serializers import (SupplierSerializer, SupplierTransactionSerializer, SupplierPaymentSerializer)
from .service.stats import get_supplier_transactions_with_stats, SupplierStatsService
from .service.supplier import SupplierService


@extend_schema(tags=["Supplier"])
class SupplierViewSet(BaseUserViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer

    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name"]
    ordering = ["full_name"]

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


@extend_schema(tags=["Supplier"])
class SupplierPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierPaymentSerializer

    def post(self, request):
        serializer = SupplierPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supplier = SupplierService.make_payment(
            supplier_id=serializer.validated_data["supplier_id"],
            amount=serializer.validated_data["amount"]
        )

        return Response(SupplierSerializer(supplier).data, status=status.HTTP_200_OK)


@extend_schema(tags=["Supplier"])
class SupplierTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierTransactionSerializer

    def get(self, request, supplier_id):
        supplier, transactions, stats = get_supplier_transactions_with_stats(supplier_id)

        serializer = SupplierTransactionSerializer(transactions, many=True)

        return Response({
            "stats": stats,
            "transactions": serializer.data
        })


@extend_schema(tags=["SupplierStats"])
class SupplierDebtStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = SupplierStatsService.get_debt_stats()
        return Response(stats)
