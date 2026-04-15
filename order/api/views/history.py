from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from order.api.serializers import OrderHistorySerializer
from order.models import OrderHistory


@extend_schema(tags=["OrderHistory"])
class OrderHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderHistorySerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = OrderHistory.objects.select_related("user", "order")

        if user:
            return queryset

        return queryset.none()
