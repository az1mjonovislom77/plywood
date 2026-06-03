from decimal import Decimal
from collections import defaultdict, deque
from django.db.models import Sum, Value, DecimalField, F, ExpressionWrapper, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from category.models import Category
from product.models import Product
from acceptance.models import Acceptance
from order.models import Order, OrderItem


class MaterialReportJsonService:
    @staticmethod
    def _money_field():
        return DecimalField(max_digits=18, decimal_places=2)

    @classmethod
    def _money_expr(cls, left, right):
        return ExpressionWrapper(F(left) * F(right), output_field=cls._money_field())

    @staticmethod
    def _accepted_order_filter():
        return Q(order__order_status=Order.OrderStatus.ACCEPT)

    @staticmethod
    def _accepted_order_before_filter(start_dt):
        return Q(order__accepted_at__lt=start_dt) | Q(order__accepted_at__isnull=True, order__created_at__lt=start_dt)

    @staticmethod
    def _accepted_order_range_filter(start_dt, end_dt):
        return Q(order__accepted_at__gte=start_dt, order__accepted_at__lt=end_dt) | Q(
            order__accepted_at__isnull=True,
            order__created_at__gte=start_dt,
            order__created_at__lt=end_dt,
        )

    @staticmethod
    def _accepted_order_until_filter(end_dt):
        return Q(order__accepted_at__lt=end_dt) | Q(order__accepted_at__isnull=True, order__created_at__lt=end_dt)

    @staticmethod
    def _sale_date(row):
        return row["order__accepted_at"] or row["order__created_at"]

    @classmethod
    def _parse_bounds(cls, date_from, date_to):
        today = timezone.localdate()
        start_date = parse_date(date_from) if date_from else today
        end_date = parse_date(date_to) if date_to else today

        if not start_date or not end_date:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        if end_date < start_date:
            raise ValueError("to date must be greater than or equal to from date")

        start_dt = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
        end_dt = timezone.make_aware(
            timezone.datetime.combine(end_date + timezone.timedelta(days=1), timezone.datetime.min.time())
        )
        return start_date, end_date, start_dt, end_dt

    @staticmethod
    def _to_qty_map(qs, qty_field):
        data = {}
        for row in qs:
            data[row["product_id"]] = Decimal(str(row[qty_field] or 0))
        return data

    @classmethod
    def _calc_fifo(cls, start_dt, end_dt, end_date):
        stock_map = defaultdict(deque)

        acceptance_rows = (
            Acceptance.objects
            .filter(acceptance_status="accept", arrival_date__lte=end_date)
            .values("product_id", "count", "arrival_price", "arrival_price_in_sum", "arrival_price_in_dollar", "arrival_date", "id")
            .order_by("product_id", "arrival_date", "id")
        )
        for row in acceptance_rows:
            stock_map[row["product_id"]].append({
                "qty": Decimal(str(row["count"])),
                "price_uzs": Decimal(str(row["arrival_price_in_sum"])),
                "price_usd": Decimal(str(row["arrival_price_in_dollar"])),
            })

        sale_rows = list(
            OrderItem.objects
            .filter(
                cls._accepted_order_filter(),
                cls._accepted_order_until_filter(end_dt),
            )
            .values("product_id", "quantity", "order__created_at", "order__accepted_at", "id")
        )
        sale_rows.sort(key=lambda r: (r["product_id"], cls._sale_date(r), r["id"]))

        open_cogs_sum_map = defaultdict(lambda: Decimal("0"))
        open_cogs_usd_map = defaultdict(lambda: Decimal("0"))
        period_cogs_sum_map = defaultdict(lambda: Decimal("0"))
        period_cogs_usd_map = defaultdict(lambda: Decimal("0"))

        for row in sale_rows:
            product_id = row["product_id"]
            qty = Decimal(str(row["quantity"]))
            sale_date = cls._sale_date(row)
            cogs_uzs = Decimal("0")
            cogs_usd = Decimal("0")
            remaining = qty
            while remaining > 0 and stock_map[product_id]:
                batch = stock_map[product_id][0]
                take = min(remaining, batch["qty"])
                cogs_uzs += take * batch["price_uzs"]
                cogs_usd += take * batch["price_usd"]
                batch["qty"] -= take
                remaining -= take
                if batch["qty"] <= 0:
                    stock_map[product_id].popleft()

            if sale_date < start_dt:
                open_cogs_sum_map[product_id] += cogs_uzs
                open_cogs_usd_map[product_id] += cogs_usd
            elif sale_date < end_dt:
                period_cogs_sum_map[product_id] += cogs_uzs
                period_cogs_usd_map[product_id] += cogs_usd

        return open_cogs_sum_map, open_cogs_usd_map, period_cogs_sum_map, period_cogs_usd_map

    @staticmethod
    def _num(v):
        return float(v or 0)

    @classmethod
    def build(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = cls._parse_bounds(date_from, date_to)
        categories = list(Category.objects.all().order_by("name"))
        products = list(Product.objects.select_related("category").order_by("category__name", "name"))
        open_in_qty_map = cls._to_qty_map(
            Acceptance.objects.filter(acceptance_status="accept", arrival_date__lt=start_date)
            .values("product_id")
            .annotate(qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field())),
            "qty",
        )
        open_in_sum_map = {}
        for row in (
                Acceptance.objects.filter(acceptance_status="accept", arrival_date__lt=start_date)
                        .values("product_id")
                        .annotate(total=Coalesce(Sum("arrival_price_in_sum"), Value(Decimal("0")),
                                                 output_field=cls._money_field()))
        ):
            open_in_sum_map[row["product_id"]] = Decimal(str(row["total"] or 0))

        open_out_qty_map = cls._to_qty_map(
            OrderItem.objects.filter(
                cls._accepted_order_filter(),
                cls._accepted_order_before_filter(start_dt),
            )
            .values("product_id")
            .annotate(qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field())),
            "qty",
        )

        in_qty_map = cls._to_qty_map(
            Acceptance.objects.filter(
                acceptance_status="accept",
                arrival_date__gte=start_date,
                arrival_date__lte=end_date)
            .values("product_id")
            .annotate(qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field())),
            "qty",
        )
        in_sum_map = {}
        for row in (
                Acceptance.objects.filter(
                    acceptance_status="accept",
                    arrival_date__gte=start_date,
                    arrival_date__lte=end_date).values("product_id")
                        .annotate(total=Coalesce(Sum("arrival_price_in_sum"), Value(Decimal("0")),
                                                 output_field=cls._money_field()))):
            in_sum_map[row["product_id"]] = Decimal(str(row["total"] or 0))

        out_qty_map = cls._to_qty_map(
            OrderItem.objects.filter(
                cls._accepted_order_filter(),
                cls._accepted_order_range_filter(start_dt, end_dt),
            )
            .values("product_id")
            .annotate(qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field())),
            "qty",
        )

        open_cogs_sum_map, open_cogs_usd_map, period_cogs_sum_map, period_cogs_usd_map = cls._calc_fifo(start_dt, end_dt, end_date)

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
                pid = product.id
                open_in_qty = open_in_qty_map.get(pid, Decimal("0"))
                open_in_sum = open_in_sum_map.get(pid, Decimal("0"))
                open_out_qty = open_out_qty_map.get(pid, Decimal("0"))
                open_out_sum = open_cogs_sum_map[pid]
                in_qty = in_qty_map.get(pid, Decimal("0"))
                in_sum = in_sum_map.get(pid, Decimal("0"))
                out_qty = out_qty_map.get(pid, Decimal("0"))
                out_sum = period_cogs_sum_map[pid]
                open_quantity = open_in_qty - open_out_qty
                open_sum = open_in_sum - open_out_sum
                end_quantity = open_quantity + in_qty - out_qty
                end_sum = open_sum + in_sum - out_sum

                item = {
                    "id": pid,
                    "name": product.name,
                    "unit": getattr(product, "unit", "дона"),
                    "opening_balance_quantity": cls._num(open_quantity),
                    "opening_balance_sum": cls._num(open_sum),
                    "received_quantity": cls._num(in_qty),
                    "received_sum": cls._num(in_sum),
                    "issued_quantity": cls._num(out_qty),
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
