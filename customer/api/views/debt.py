from django.core.exceptions import ValidationError
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from customer.api.serializers import CoverDebtSerializer, CustomerHistoryResponseSerializer
from customer.models import Customer
from customer.service.cover_debt import DebtService
from customer.service.statement_service import CustomerStatementService


@extend_schema(tags=["CustomerDebt"])
class CoverDebtAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CoverDebtSerializer

    def post(self, request, pk):
        serializer = CoverDebtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            customer = DebtService.cover_debt(customer_id=pk, amount=serializer.validated_data["amount"])
            return Response({"message": "Debt covered", "current_debt": customer.debt}, status=status.HTTP_200_OK)
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


@extend_schema(
    tags=["CustomerDebt"],
    parameters=[
        OpenApiParameter(name="from", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
        OpenApiParameter(name="to", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY)])
class CustomerStatementExcelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        try:
            content = CustomerStatementService.build_statement_excel(pk, date_from=date_from, date_to=date_to)
        except Customer.DoesNotExist:
            return Response({"detail": "Customer not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(
            content.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="customer_{pk}_statement.xlsx"'
        return response
