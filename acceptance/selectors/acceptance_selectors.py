from acceptance.models import Acceptance, AcceptanceHistory


class AcceptanceSelector:
    @staticmethod
    def acceptance_queryset():
        return Acceptance.objects.select_related("product", "supplier", "accepted_by").prefetch_related("histories")

    @staticmethod
    def history_queryset():
        return AcceptanceHistory.objects.select_related("product", "acceptance")
