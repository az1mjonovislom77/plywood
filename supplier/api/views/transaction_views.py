from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from supplier.api.serializers import SupplierTransactionSerializer
from supplier.service.stats import get_supplier_transactions_with_stats


@extend_schema(tags=["Supplier"])
class SupplierTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, supplier_id):
        supplier, transactions, stats = get_supplier_transactions_with_stats(supplier_id)
        serializer = SupplierTransactionSerializer(transactions, many=True)
        return Response({"stats": stats, "transactions": serializer.data})
