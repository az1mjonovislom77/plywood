from drf_spectacular.utils import extend_schema
from rest_framework import filters
from supplier.api.serializers import SupplierSerializer
from supplier.models import Supplier
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
