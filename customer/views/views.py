from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from customer.models import Customer
from rest_framework import filters, status
from customer.serializers import CustomerSerializer, CoverDebtSerializer, CustomerHistoryResponseSerializer
from customer.service.cover_debt import DebtService
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Customer"])
class CustomerViewSet(BaseUserViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    ordering = ['-id']

    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']


@extend_schema(tags=["CustomerDebt"])
class CoverDebtAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CoverDebtSerializer

    def post(self, request, pk):
        serializer = CoverDebtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            customer = DebtService.cover_debt(customer_id=pk, amount=serializer.validated_data["amount"])
            return Response(
                {"message": "Debt covered", "current_debt": customer.debt}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["CustomerDebt"])
class CustomerHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerHistoryResponseSerializer

    def get(self, request, pk):
        data = DebtService.get_customer_history(pk)

        serializer = CustomerHistoryResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
