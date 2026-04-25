from django.http import HttpResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet
from supplier.api.serializers import SupplierSerializer
from supplier.models import Supplier
from supplier.service.supplier_export import SupplierStatementService, SupplierSalesStatementService
from utils.base.views_base import BaseUserViewSet


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


@extend_schema(
    tags=["SupplierExport"],
    parameters=[
        OpenApiParameter(name="supplier_id", required=False, type=int),
        OpenApiParameter(name="date_from", required=False, type=str),
        OpenApiParameter(name="date_to", required=False, type=str),
    ],
)
class SupplierStatementExcelViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        supplier_id = request.query_params.get("supplier_id")
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if supplier_id:
            file = SupplierStatementService.build_statement_excel(supplier_id=int(supplier_id), date_from=date_from,
                                                                  date_to=date_to)
            filename = f"supplier_{supplier_id}_statement.xlsx"

        else:
            file = SupplierSalesStatementService.build_statement_excel(supplier_id=None, date_from=date_from,
                                                                       date_to=date_to)
            filename = "supplier_sales_all.xlsx"

        return HttpResponse(
            file.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
