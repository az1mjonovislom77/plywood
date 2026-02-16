from drf_spectacular.utils import extend_schema
from customer.models import Customer
from rest_framework import filters
from customer.serializers import CustomerSerializer
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Customer"])
class CustomerViewSet(BaseUserViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()
    ordering = ['-id']

    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']
