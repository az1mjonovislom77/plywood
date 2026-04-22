from django.db.models import Prefetch
from acceptance.models import Acceptance, AcceptanceHistory


class AcceptanceSelector:
    @staticmethod
    def acceptance_queryset():
        return Acceptance.objects.select_related("product", "supplier", "accepted_by").prefetch_related("histories")

    @staticmethod
    def history_queryset():
        return AcceptanceHistory.objects.select_related("product", "acceptance")

    @staticmethod
    def supplier_acceptances_queryset(supplier_id, date):
        history_queryset = AcceptanceHistory.objects.select_related("user", "supplier", "product")
        return (
            Acceptance.objects
            .filter(supplier_id=supplier_id, created_at__date=date)
            .select_related("product", "supplier", "accepted_by")
            .prefetch_related(Prefetch("histories", queryset=history_queryset))
            .order_by("-created_at")
        )
