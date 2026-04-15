from drf_spectacular.utils import extend_schema
from order.api.serializers import ThicknessSerializer
from order.models import Thickness
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Thickness"])
class ThicknessViewSet(BaseUserViewSet):
    queryset = Thickness.objects.all()
    serializer_class = ThicknessSerializer
    ordering = ["-id"]
