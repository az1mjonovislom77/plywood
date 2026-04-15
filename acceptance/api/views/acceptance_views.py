from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from acceptance.api.serializers import AcceptanceCancelSerializer, AcceptanceSerializer
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
