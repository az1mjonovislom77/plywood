from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from acceptance.api.serializers import AcceptanceCancelSerializer, AcceptanceSerializer, SupplierAcceptanceSerializer
from acceptance.selectors.acceptance_selectors import AcceptanceSelector
from acceptance.service.acceptance_workflow import AcceptanceWorkflowService
from utils.base.views_base import BaseUserViewSet


@extend_schema(tags=["Acceptance"])
class AcceptanceViewSet(BaseUserViewSet):
    queryset = AcceptanceSelector.acceptance_queryset()
    serializer_class = AcceptanceSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        acceptance = AcceptanceWorkflowService.create(data=serializer.validated_data, user=self.request.user)
        serializer.instance = acceptance

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        try:
            acceptance = AcceptanceWorkflowService.accept(acceptance_id=pk, user=request.user)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        serializer = self.get_serializer(acceptance)
        return Response(serializer.data)

    @extend_schema(request=AcceptanceCancelSerializer)
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        description = request.data.get("description")
        try:
            acceptance = AcceptanceWorkflowService.cancel(pk, request.user, description)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        serializer = self.get_serializer(acceptance)
        return Response(serializer.data)

    @extend_schema(parameters=[
        OpenApiParameter(name="date", type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY),
    ])
    @action(detail=False, methods=["get"], url_path=r"supplier/(?P<supplier_id>\d+)")
    def supplier_acceptances(self, request, supplier_id=None):
        date_param = request.query_params.get("date")

        if date_param:
            selected_date = parse_date(date_param)
            if not selected_date:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD"}, status=400)
        else:
            selected_date = timezone.localdate()

        queryset = AcceptanceSelector.supplier_acceptances_queryset(supplier_id=supplier_id, date=selected_date)
        serializer = SupplierAcceptanceSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)
