from decimal import Decimal
from django.db.models import Sum, Value, DecimalField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from category.models import Category
from product.models import Product
from acceptance.models import Acceptance
from order.models import OrderItem


class MaterialReportJsonService:
    @staticmethod
    def _money_field():
        return DecimalField(max_digits=18, decimal_places=2)

    @classmethod
    def _money_expr(cls, left, right):
        return ExpressionWrapper(F(left) * F(right), output_field=cls._money_field())

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
                "quantity": Decimal(str(row["movement_quantity"] or 0)),
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
                movement_quantity=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(Sum(cls._money_expr("count", "arrival_price")), Value(Decimal("0")),
                               output_field=cls._money_field()),
            )
        )

        open_out_map = cls._to_map(
            OrderItem.objects.filter(order__created_at__lt=start_dt)
            .values("product_id").annotate(
                movement_quantity=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(Sum(cls._money_expr("quantity", "price")), Value(Decimal("0")),
                               output_field=cls._money_field()),
            )
        )

        in_map = cls._to_map(
            Acceptance.objects.filter(acceptance_status="accept", created_at__gte=start_dt, created_at__lt=end_dt)
            .values("product_id").annotate(
                movement_quantity=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(Sum(cls._money_expr("count", "arrival_price")), Value(Decimal("0")),
                               output_field=cls._money_field()),
            )
        )

        out_map = cls._to_map(
            OrderItem.objects.filter(order__created_at__gte=start_dt, order__created_at__lt=end_dt)
            .values("product_id").annotate(
                movement_quantity=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(Sum(cls._money_expr("quantity", "price")), Value(Decimal("0")),
                               output_field=cls._money_field()),
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
                "opening_balance_quantity": 0,
                "opening_balance_sum": 0,
                "received_quantity": 0,
                "received_sum": 0,
                "issued_quantity": 0,
                "issued_sum": 0,
                "closing_balance_quantity": 0,
                "closing_balance_sum": 0,
            },
        }

        for category in categories:
            category_products = grouped_products.get(category.id, [])
            if not category_products:
                continue

            cat_data = {
                "id": category.id,
                "name": category.name,
                "opening_balance_quantity": 0,
                "opening_balance_sum": 0,
                "received_quantity": 0,
                "received_sum": 0,
                "issued_quantity": 0,
                "issued_sum": 0,
                "closing_balance_quantity": 0,
                "closing_balance_sum": 0,
                "products": [],
            }

            for product in category_products:
                open_in = open_in_map.get(product.id, {"quantity": Decimal("0"), "total": Decimal("0")})
                open_out = open_out_map.get(product.id, {"quantity": Decimal("0"), "total": Decimal("0")})
                in_period = in_map.get(product.id, {"quantity": Decimal("0"), "total": Decimal("0")})
                out_period = out_map.get(product.id, {"quantity": Decimal("0"), "total": Decimal("0")})
                open_quantity = open_in["quantity"] - open_out["quantity"]
                open_sum = open_in["total"] - open_out["total"]
                in_quantity = in_period["quantity"]
                in_sum = in_period["total"]
                out_quantity = out_period["quantity"]
                out_sum = out_period["total"]
                end_quantity = open_quantity + in_quantity - out_quantity
                end_sum = open_sum + in_sum - out_sum

                item = {
                    "id": product.id,
                    "name": product.name,
                    "unit": getattr(product, "unit", "дона"),
                    "opening_balance_quantity": cls._num(open_quantity),
                    "opening_balance_sum": cls._num(open_sum),
                    "received_quantity": cls._num(in_quantity),
                    "received_sum": cls._num(in_sum),
                    "issued_quantity": cls._num(out_quantity),
                    "issued_sum": cls._num(out_sum),
                    "closing_balance_quantity": cls._num(end_quantity),
                    "closing_balance_sum": cls._num(end_sum),
                }

                cat_data["products"].append(item)
                cat_data["opening_balance_quantity"] += item["opening_balance_quantity"]
                cat_data["opening_balance_sum"] += item["opening_balance_sum"]
                cat_data["received_quantity"] += item["received_quantity"]
                cat_data["received_sum"] += item["received_sum"]
                cat_data["issued_quantity"] += item["issued_quantity"]
                cat_data["issued_sum"] += item["issued_sum"]
                cat_data["closing_balance_quantity"] += item["closing_balance_quantity"]
                cat_data["closing_balance_sum"] += item["closing_balance_sum"]

            result["categories"].append(cat_data)
            result["totals"]["opening_balance_quantity"] += cat_data["opening_balance_quantity"]
            result["totals"]["opening_balance_sum"] += cat_data["opening_balance_sum"]
            result["totals"]["received_quantity"] += cat_data["received_quantity"]
            result["totals"]["received_sum"] += cat_data["received_sum"]
            result["totals"]["issued_quantity"] += cat_data["issued_quantity"]
            result["totals"]["issued_sum"] += cat_data["issued_sum"]
            result["totals"]["closing_balance_quantity"] += cat_data["closing_balance_quantity"]
            result["totals"]["closing_balance_sum"] += cat_data["closing_balance_sum"]

        return result
