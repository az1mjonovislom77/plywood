from django.db import transaction
from django.db.models import F
from django.utils import timezone
from acceptance.models import Acceptance, AcceptanceHistory
from product.models import Product


class AcceptanceWorkflowService:

    @staticmethod
    @transaction.atomic
    def cancel(acceptance_id, user, description=None):
        acceptance = Acceptance.objects.select_for_update().get(id=acceptance_id)

        if acceptance.acceptance_status != Acceptance.AcceptanceStatus.WAITING:
            raise ValueError("Acceptance already closed")

        acceptance.acceptance_status = Acceptance.AcceptanceStatus.CANCEL
        acceptance.save(update_fields=["acceptance_status"])

        items = acceptance.items.all().only("product_id", "quantity")

        for item in items:
            Product.objects.filter(id=item.product_id).update(count=F("count") + item.quantity)

        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.CANCEL,
            description=description
        )

        return acceptance

    @staticmethod
    @transaction.atomic
    def accept(acceptance_id, user):
        acceptance = Acceptance.objects.select_for_update().get(id=acceptance_id)

        if acceptance.acceptance_status != Acceptance.AcceptanceStatus.WAITING:
            raise ValueError("Acceptance already processed")

        acceptance.acceptance_status = Acceptance.AcceptanceStatus.ACCEPT
        acceptance.accepted_by = user
        acceptance.accepted_at = timezone.now()

        acceptance.save(update_fields=[
            "acceptance_status",
            "accepted_by",
            "accepted_at",
        ])

        AcceptanceHistory.objects.create(
            acceptance=acceptance,
            user=user,
            action=AcceptanceHistory.Action.ACCEPT
        )

        return acceptance
