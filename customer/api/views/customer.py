from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from customer.api.serializers import CustomerSerializer
from customer.models import Customer
from customer.service.customer_balance import CustomerBalanceService
from customer.service.customer_export import SalesStatementService
from customer.service.customers_debt_export import CustomerDebtExcelService
from customer.service.statement_service import CustomerStatementService
from utils.base.views_base import BaseUserViewSet
from utils.search import TransliteratedSearchFilter


@extend_schema(tags=["Customer"])
class CustomerViewSet(BaseUserViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    ordering = ['-id']
    filter_backends = [TransliteratedSearchFilter]
    search_fields = ['full_name', 'phone_number']

    def retrieve(self, request, *args, **kwargs):
        customer_id = kwargs.get("pk")
        CustomerBalanceService.sync_customer_debt(customer_id)

        return super().retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        date_from = request.GET.get("from")
        date_to = request.GET.get("to")
        customers = self.filter_queryset(self.get_queryset())

        results = []

        for customer in customers:
            if date_from and date_to:
                debt = (CustomerBalanceService
                        .calculate_customer_debt(customer=customer, date_from=date_from, date_to=date_to))

            else:
                CustomerBalanceService.sync_customer_debt(customer.id)
                customer.refresh_from_db()
                debt = customer.debt
            data = CustomerSerializer(customer).data
            data["debt"] = debt
            results.append(data)

        return Response(results)


@extend_schema(
    tags=["CustomerExport"],
    parameters=[
        OpenApiParameter(name="customer_id", required=False, type=int),
        OpenApiParameter(name="from", required=False, type=str),
        OpenApiParameter(name="to", required=False, type=str),
    ],
)
class CustomerStatementExcelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        customer_id = request.query_params.get("customer_id")
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        if customer_id:
            file = CustomerStatementService.build_statement_excel(customer_id=int(customer_id), date_from=date_from,
                                                                  date_to=date_to)
            filename = f"customer_{customer_id}_statement.xlsx"

        else:
            file = SalesStatementService.build_statement_excel(customer_id=None, date_from=date_from, date_to=date_to)
            filename = "customer_sales_all.xlsx"

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )


@extend_schema(tags=["Customer"])
class CustomerDebtExcelAPIView(APIView):

    def get(self, request):
        return CustomerDebtExcelService.response()
