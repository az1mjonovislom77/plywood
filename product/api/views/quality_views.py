from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from product.api.serializers import QualitySerializer
from product.models import Quality
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Quality"])
class QualityViewSet(BaseUserViewSet):
    queryset = Quality.objects.all()
    serializer_class = QualitySerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]
    pagination_class = None
    ordering = ["-id"]
