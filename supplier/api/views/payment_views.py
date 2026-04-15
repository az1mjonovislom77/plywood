from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from supplier.api.serializers import SupplierPaymentSerializer, SupplierSerializer
from supplier.service.supplier import SupplierService


@extend_schema(tags=["Supplier"])
class SupplierPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupplierPaymentSerializer

    def post(self, request):
        serializer = SupplierPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supplier = SupplierService.make_payment(
            supplier_id=serializer.validated_data["supplier_id"],
            amount=serializer.validated_data["amount"],
        )

        return Response(SupplierSerializer(supplier).data, status=status.HTTP_200_OK)
