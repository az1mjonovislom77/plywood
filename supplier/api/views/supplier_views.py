from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.exceptions import ValidationError
from supplier.api.serializers import SupplierSerializer
from supplier.selectors.supplier_selectors import SupplierSelector
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Supplier"])
class SupplierViewSet(BaseUserViewSet):
    serializer_class = SupplierSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["full_name"]
    ordering = ["full_name"]

    def get_queryset(self):
        date_param = self.request.query_params.get("date")

        if date_param:
            selected_date = parse_date(date_param)
            if not selected_date:
                raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD"})
        else:
            selected_date = timezone.localdate()

        return SupplierSelector.suppliers_with_daily_acceptance_stats(selected_date)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])
