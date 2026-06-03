from django.db.models import Prefetch, Sum, ExpressionWrapper, F, DecimalField
from django.db.models.functions import TruncDate

from acceptance.models import Acceptance, AcceptanceHistory


class AcceptanceSelector:
    @staticmethod
    def _date_annotation(date_field):
        if date_field == "arrival_date":
            return F(date_field)
        return TruncDate(date_field)

    @staticmethod
    def acceptance_queryset():
        history_queryset = AcceptanceHistory.objects.select_related("user", "supplier", "product")
        return (
            Acceptance.objects
            .select_related("product", "supplier", "accepted_by")
            .prefetch_related(Prefetch("histories", queryset=history_queryset))
        )

    @staticmethod
    def history_queryset():
        return AcceptanceHistory.objects.select_related("product", "acceptance", "user")

    @staticmethod
    def supplier_acceptances_queryset(supplier_id, date):
        history_queryset = AcceptanceHistory.objects.select_related("user", "supplier", "product")
        return (
            Acceptance.objects
            .filter(supplier_id=supplier_id, arrival_date=date)
            .select_related("product", "supplier", "accepted_by")
            .prefetch_related(Prefetch("histories", queryset=history_queryset))
            .order_by("-created_at")
        )

    @staticmethod
    def grouped_supplier_stats_queryset(date_field="created_at", from_date=None, to_date=None, supplier_id=None):
        qs = Acceptance.objects.filter(acceptance_status=Acceptance.AcceptanceStatus.ACCEPT, supplier__isnull=False)
        
        if from_date:
            qs = qs.filter(**{f"{date_field}__gte": from_date})
        if to_date:
            qs = qs.filter(**{f"{date_field}__lte": to_date})
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
            
        return (
            qs
            .annotate(date=AcceptanceSelector._date_annotation(date_field))
            .values("date", "supplier_id", "supplier__full_name")
            .annotate(
                total_quantity=Sum("count"),
                total_investment=Sum(
                    ExpressionWrapper(
                        F("arrival_price") * F("count"),
                        output_field=DecimalField(max_digits=18, decimal_places=2)))).order_by("-date", "supplier_id"))

    @staticmethod
    def grouped_supplier_stats(date_field="created_at", from_date=None, to_date=None, supplier_id=None):
        qs = Acceptance.objects.filter(supplier__isnull=False)
        
        if from_date:
            qs = qs.filter(**{f"{date_field}__gte": from_date})
        if to_date:
            qs = qs.filter(**{f"{date_field}__lte": to_date})
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
            
        return (
            qs
            .annotate(date=AcceptanceSelector._date_annotation(date_field))
            .values("date", "supplier_id", "supplier__full_name")
            .annotate(
                total_quantity=Sum("count"),
                total_investment=Sum(
                    ExpressionWrapper(
                        F("arrival_price") * F("count"),
                        output_field=DecimalField(max_digits=18, decimal_places=2)))).order_by("-date", "supplier_id"))
