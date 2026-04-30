from decimal import Decimal
from django.db.models import Sum, Value, DecimalField, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from category.models import Category
from product.models import Product
from acceptance.models import Acceptance
from order.models import OrderItem


class MaterialReportJsonService:
    @classmethod
    def _parse_bounds(cls, date_from, date_to):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today

        if not start_date or not end_date:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        if end_date < start_date:
            raise ValueError("to date must be greater than or equal to from date")

        start_dt = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        end_dt = timezone.make_aware(
            timezone.datetime.combine(end_date + timezone.timedelta(days=1), timezone.datetime.min.time())
        )
        return start_date, end_date, start_dt, end_dt

    @staticmethod
    def _to_map(qs):
        data = {}
        for row in qs:
            data[row["product_id"]] = {
                "qty": Decimal(str(row["qty"] or 0)),
                "total": Decimal(str(row["total"] or 0)),
            }
        return data

    @staticmethod
    def _num(v):
        return float(v or 0)

    @classmethod
    def build(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = cls._parse_bounds(date_from, date_to)

        categories = list(Category.objects.all().order_by("name"))
        products = list(Product.objects.select_related("category").order_by("category__name", "name"))

        open_in_map = cls._to_map(
            Acceptance.objects.filter(acceptance_status="accept", created_at__lt=start_dt)
            .values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("count") * F("arrival_price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        open_out_map = cls._to_map(
            OrderItem.objects.filter(order__created_at__lt=start_dt)
            .values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("quantity") * F("price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        in_map = cls._to_map(
            Acceptance.objects.filter(acceptance_status="accept", created_at__gte=start_dt, created_at__lt=end_dt)
            .values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("count") * F("arrival_price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        out_map = cls._to_map(
            OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lt=end_dt)
            .values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("quantity") * F("price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        grouped_products = {}
        for product in products:
            grouped_products.setdefault(product.category_id, []).append(product)

        result = {
            "from": str(start_date),
            "to": str(end_date),
            "categories": [],
            "totals": {
                "open_qty": 0,
                "open_sum": 0,
                "in_qty": 0,
                "in_sum": 0,
                "out_qty": 0,
                "out_sum": 0,
                "end_qty": 0,
                "end_sum": 0,
            },
        }

        for category in categories:
            category_products = grouped_products.get(category.id, [])
            if not category_products:
                continue

            cat_data = {
                "id": category.id,
                "name": category.name,
                "open_qty": 0,
                "open_sum": 0,
                "in_qty": 0,
                "in_sum": 0,
                "out_qty": 0,
                "out_sum": 0,
                "end_qty": 0,
                "end_sum": 0,
                "products": [],
            }

            for product in category_products:
                open_in = open_in_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                open_out = open_out_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                in_period = in_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                out_period = out_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                open_qty = open_in["qty"] - open_out["qty"]
                open_sum = open_in["total"] - open_out["total"]
                in_qty = in_period["qty"]
                in_sum = in_period["total"]
                out_qty = out_period["qty"]
                out_sum = out_period["total"]
                end_qty = open_qty + in_qty - out_qty
                end_sum = open_sum + in_sum - out_sum

                item = {
                    "id": product.id,
                    "name": product.name,
                    "unit": getattr(product, "unit", "дона"),
                    "open_qty": cls._num(open_qty),
                    "open_sum": cls._num(open_sum),
                    "in_qty": cls._num(in_qty),
                    "in_sum": cls._num(in_sum),
                    "out_qty": cls._num(out_qty),
                    "out_sum": cls._num(out_sum),
                    "end_qty": cls._num(end_qty),
                    "end_sum": cls._num(end_sum),
                }

                cat_data["products"].append(item)
                cat_data["open_qty"] += item["open_qty"]
                cat_data["open_sum"] += item["open_sum"]
                cat_data["in_qty"] += item["in_qty"]
                cat_data["in_sum"] += item["in_sum"]
                cat_data["out_qty"] += item["out_qty"]
                cat_data["out_sum"] += item["out_sum"]
                cat_data["end_qty"] += item["end_qty"]
                cat_data["end_sum"] += item["end_sum"]

            result["categories"].append(cat_data)
            result["totals"]["open_qty"] += cat_data["open_qty"]
            result["totals"]["open_sum"] += cat_data["open_sum"]
            result["totals"]["in_qty"] += cat_data["in_qty"]
            result["totals"]["in_sum"] += cat_data["in_sum"]
            result["totals"]["out_qty"] += cat_data["out_qty"]
            result["totals"]["out_sum"] += cat_data["out_sum"]
            result["totals"]["end_qty"] += cat_data["end_qty"]
            result["totals"]["end_sum"] += cat_data["end_sum"]

        return result
