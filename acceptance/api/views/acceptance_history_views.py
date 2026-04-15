from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from acceptance.api.serializers import AcceptanceHistorySerializer
from acceptance.selectors.acceptance_selectors import AcceptanceSelector


@extend_schema(tags=["AcceptanceHistory"])
class AcceptanceHistoryViewSet(ModelViewSet):
    queryset = AcceptanceSelector.history_queryset()
    serializer_class = AcceptanceHistorySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]
    pagination_class = None
