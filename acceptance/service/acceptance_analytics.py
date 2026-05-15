from collections import OrderedDict

from acceptance.selectors.acceptance_selectors import AcceptanceSelector


class AcceptanceAnalyticsService:

    @staticmethod
    def get_grouped_supplier_stats(date_field="created_at", from_date=None, to_date=None, supplier_id=None):
        qs = AcceptanceSelector.grouped_supplier_stats_queryset(date_field=date_field, from_date=from_date,
                                                                to_date=to_date, supplier_id=supplier_id)

        grouped = OrderedDict()

        for item in qs:
            date = item["date"]

            if date not in grouped:
                grouped[date] = []

            grouped[date].append({
                "supplier_id": item["supplier_id"],
                "supplier_name": item["supplier__full_name"],
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

    @staticmethod
    def get_grouped_suppliers(date_field="created_at", from_date=None, to_date=None, supplier_id=None):
        qs = AcceptanceSelector.grouped_supplier_stats(date_field=date_field, from_date=from_date, to_date=to_date,
                                                       supplier_id=supplier_id)

        grouped = OrderedDict()

        for item in qs:
            date = item["date"]

            if date not in grouped:
                grouped[date] = []

            grouped[date].append({
                "supplier_id": item["supplier_id"],
                "supplier_name": item["supplier__full_name"],
                "total_quantity": item["total_quantity"] or 0,
                "total_investment": item["total_investment"] or 0,
            })

        return [
            {
                "date": date,
                "suppliers": suppliers
            } for date, suppliers in grouped.items()
        ]
