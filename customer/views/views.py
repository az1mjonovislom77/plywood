from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from customer.models import Customer, Payment
from rest_framework import filters, status
from customer.serializers import CustomerSerializer, CoverDebtSerializer, PaymentHistorySerializer
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
    serializer_class = CoverDebtSerializer

    def post(self, request, pk):
        serializer = CoverDebtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            customer, payment = DebtService.cover_debt(customer_id=pk, amount=serializer.validated_data["amount"])

            return Response({
                "remaining_debt": customer.debt,
                "total_covered": customer.covered_debt,
                "payment_id": payment.id
            }, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["CustomerDebt"])
class CustomerPaymentHistoryAPIView(ListAPIView):
    serializer_class = PaymentHistorySerializer
    pagination_class = None

    def get_queryset(self):
        return Payment.objects.filter(customer_id=self.kwargs["pk"])
