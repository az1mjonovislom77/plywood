from django.http import HttpResponse
from math import ceil
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ViewSet
from customer.api.serializers import CustomerSerializer
from customer.service.customer_export import SalesStatementService
from customer.service.customers_debt_export import CustomerDebtExcelService
from customer.service.statement_service import CustomerStatementService
from utils.base.views_base import BaseUserViewSet
from utils.search import TransliteratedSearchFilter
from decimal import Decimal
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.response import Response
from customer.models import Customer
from customer.service.customer_balance import CustomerBalanceService


class CustomerPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "limit"

    def get_paginated_response(self, data):
        total = self.page.paginator.count
        limit = self.get_page_size(self.request)

        return Response({
            "page": self.page.number,
            "limit": limit,
            "total": total,
            "total_pages": ceil(total / limit) if limit else 0,
            "data": data,
        })


@extend_schema(tags=["Customer"],
               parameters=[
                   OpenApiParameter(name="from", required=False, type=str),
                   OpenApiParameter(name="to", required=False, type=str),
                   OpenApiParameter(name="page", required=False, type=int),
                   OpenApiParameter(name="limit", required=False, type=int)])
class CustomerViewSet(BaseUserViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    ordering = ['-id']
    pagination_class = CustomerPagination
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
        page = self.paginate_queryset(customers)
        customers_to_serialize = page if page is not None else customers
        customers_to_serialize = list(customers_to_serialize)
        customer_ids = [customer.id for customer in customers_to_serialize]

        if date_from and date_to:
            debt_map = CustomerBalanceService.bulk_calculate_customer_debt(
                customers=customers_to_serialize,
                date_from=date_from,
                date_to=date_to,
            )
        else:
            stats_map = CustomerBalanceService.bulk_sync_customer_debts(customer_ids)
            debt_map = {
                customer_id: max(stats["remaining_debt"], Decimal("0"))
                for customer_id, stats in stats_map.items()
            }
            for customer in customers_to_serialize:
                remaining_debt = stats_map.get(customer.id, {}).get("remaining_debt", Decimal("0"))
                customer.debt = debt_map.get(customer.id, Decimal("0"))
                customer.overpayment = max(-remaining_debt, Decimal("0"))

        results = []

        for customer in customers_to_serialize:
            data = CustomerSerializer(customer).data
            data["debt"] = debt_map.get(customer.id, Decimal("0"))
            results.append(data)

        if page is not None:
            return self.get_paginated_response(results)

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


@extend_schema(tags=["Customer"],
               parameters=[
                   OpenApiParameter(name="from", required=False, default='2025-01-01', type=str),
                   OpenApiParameter(name="to", required=False, type=str)])
class CustomerDebtExcelAPIView(APIView):

    def get(self, request):
        return CustomerDebtExcelService.response(request)


@extend_schema(tags=["CustomerDebtJson"],
               parameters=[
                   OpenApiParameter(name="from", required=False, default='2024-01-01', type=str),
                   OpenApiParameter(name="to", required=False, type=str)])
class CustomerDebtReportJsonAPIView(APIView):

    def get(self, request):
        today = timezone.localdate()
        date_from_str = request.GET.get("from")
        if not date_from_str:
            date_from_str = '2024-01-01'

        start_date = parse_date(date_from_str)
        end_date = (parse_date(request.GET.get("to"))
                    if request.GET.get("to")
                    else today)
        customers = list(Customer.objects.all().order_by("full_name"))
        results = []
        total_dt = Decimal("0")
        total_kt = Decimal("0")
        debt_map = CustomerBalanceService.bulk_calculate_customer_debt(
            customers=customers,
            date_from=start_date,
            date_to=end_date,
        )

        for customer in customers:

            debt = debt_map.get(customer.id, Decimal("0"))
            debt = Decimal(str(debt or 0))
            debt_value = None
            overpaid_value = None

            if debt < 0:
                debt_value = abs(debt)
                total_dt += abs(debt)

            elif debt > 0:
                overpaid_value = debt
                total_kt += debt

            results.append({
                "customer_id": customer.id,
                "customer": customer.full_name,
                "overpaid": (float(overpaid_value) if overpaid_value
                             else 0),
                "debt": (float(debt_value) if debt_value
                         else 0)
            })

        return Response({
            "from": str(start_date),
            "to": str(end_date),
            "total_overpaid": float(total_kt),
            "total_debt": float(total_dt),
            "results": results
        })
