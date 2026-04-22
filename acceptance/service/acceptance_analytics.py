from collections import OrderedDict

from acceptance.selectors.acceptance_selectors import AcceptanceSelector


class AcceptanceAnalyticsService:

    @staticmethod
    def get_grouped_supplier_stats(date_field="created_at"):
        qs = AcceptanceSelector.grouped_supplier_stats_queryset(date_field=date_field)

        grouped = OrderedDict()

        for item in qs:
            date = item["date"]

            if date not in grouped:
                grouped[date] = []

            grouped[date].append({
                "supplier_id": item["supplier_id"],
                "supplier_name": item["supplier__name"],
                "total_quantity": item["total_quantity"] or 0,
                "total_investment": item["total_investment"] or 0,
            })

        return [
            {
                "date": date,
                "suppliers": suppliers
            }
            for date, suppliers in grouped.items()
        ]
