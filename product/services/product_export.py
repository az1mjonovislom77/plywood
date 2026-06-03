from io import BytesIO
from decimal import Decimal
from django.db.models import Sum, Value, DecimalField, F, ExpressionWrapper, Q, Case, When
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from category.models import Category
from product.models import Product
from acceptance.models import Acceptance
from order.models import Order, OrderItem
from product.services.export_json import MaterialReportJsonService


class MaterialReportService:
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
            timezone.datetime.combine(end_date + timezone.timedelta(days=1), timezone.datetime.min.time()))
        return start_date, end_date, start_dt, end_dt

    @staticmethod
    def _to_map(qs, extra_fields=None):
        if extra_fields is None:
            extra_fields = []
        data = {}
        for row in qs:
            product_id = row["product_id"]
            data[product_id] = {
                "qty": Decimal(str(row.get("qty") or 0)),
                "total": Decimal(str(row.get("total") or 0)),
            }
            for field in extra_fields:
                data[product_id][field] = Decimal(str(row.get(field) or 0))
        return data

    @classmethod
    def build_excel(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = cls._parse_bounds(date_from, date_to)
        categories = list(Category.objects.all().order_by("name"))
        products = list(Product.objects.select_related("category").order_by("category__name", "name"))

        open_in_map = cls._to_map(
            Acceptance.objects.filter(acceptance_status="accept", arrival_date__lt=start_date)
            .values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(
                    Sum(cls._money_expr("count", "arrival_price")), Value(Decimal("0")),
                    output_field=cls._money_field(),
                ),
            )
        )

        open_out_map = cls._to_map(
            OrderItem.objects.filter(
                cls._accepted_order_filter(), cls._accepted_order_before_filter(start_dt))
            .values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(
                    Sum(cls._money_expr("quantity", "price")),
                    Value(Decimal("0")),
                    output_field=cls._money_field(),
                ),
            )
        )

        in_map = cls._to_map(
            Acceptance.objects.filter(
                acceptance_status="accept", arrival_date__gte=start_date, arrival_date__lte=end_date,
            ).values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(
                    Sum(cls._money_expr("count", "arrival_price")),
                    Value(Decimal("0")),
                    output_field=cls._money_field())))

        out_map = cls._to_map(
            OrderItem.objects.filter(
                cls._accepted_order_filter(),
                cls._accepted_order_range_filter(start_dt, end_dt),
            ).values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=cls._money_field()),
                total=Coalesce(
                    Sum(cls._money_expr("quantity", "price")), Value(Decimal("0")),
                    output_field=cls._money_field(),
                ),
                total_in_dollar=Coalesce(
                    Sum(
                        F("quantity") * Case(
                            When(new_price_in_dollar__isnull=False, then=F("new_price_in_dollar")),
                            default=F("price_in_dollar"),
                            output_field=cls._money_field())),
                    Value(Decimal("0")),
                    output_field=cls._money_field()
                )), extra_fields=['total_in_dollar'])

        total_sales_uzs = sum(p.get('total', Decimal('0')) for p in out_map.values())
        total_sales_usd = sum(p.get('total_in_dollar', Decimal('0')) for p in out_map.values())
        effective_rate = Decimal('0')
        if total_sales_usd > 0:
            effective_rate = total_sales_uzs / total_sales_usd

        open_cogs_map, period_cogs_map = MaterialReportJsonService._calc_fifo(start_dt, end_dt, end_date)

        grouped_products = {}
        for product in products:
            grouped_products.setdefault(product.category_id, []).append(product)

        wb = Workbook()
        ws = wb.active
        ws.title = "Material Report"
        bold = Font(name="Arial", size=10, bold=True)
        normal = Font(name="Arial", size=10)
        center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        left = Alignment(horizontal="left", vertical="center", wrap_text=True)
        right = Alignment(horizontal="right", vertical="center")
        thin = Side(style="thin", color="000000")
        border = Border(left=thin, right=thin, top=thin, bottom=thin)

        def money(cell, value):
            value = float(value or 0)
            if value == int(value):
                cell.value = int(value)
                cell.number_format = "#,##0"
            else:
                cell.value = value
                cell.number_format = "#,##0.000"

        def money_with_dollar(cell, value, value_in_dollar):
            s_value = f"{float(value or 0):,.2f}".replace(",", " ").replace(".", ",")
            s_value_in_dollar = f"{float(value_in_dollar or 0):,.2f}".replace(",", " ").replace(".", ",")
            cell.value = f"{s_value} ({s_value_in_dollar}$)"
            cell.alignment = right

        ws.merge_cells("B1:L1")
        ws["B1"] = f"Материальный отчет за {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        ws["B1"].font = Font(name="Arial", size=14, bold=True)
        ws["B1"].alignment = left
        ws["B3"] = "Склад"
        ws["B3"].font = Font(name="Arial", size=14, bold=True)
        ws["F3"] = "Асосий РМУ"
        ws["F3"].font = Font(name="Arial", size=18)
        ws["F3"].alignment = left
        ws.merge_cells("A4:A6")
        ws.merge_cells("B4:D6")
        ws.merge_cells("E4:E6")
        ws.merge_cells("F4:G4")
        ws.merge_cells("H4:I4")
        ws.merge_cells("J4:K4")
        ws.merge_cells("L4:M4")
        ws["A4"] = "Код"
        ws["B4"] = "МатериалРодитель / Материал"
        ws["E4"] = "Ед.изм"
        ws["F4"] = "Сальдо на начало"
        ws["H4"] = "Приход"
        ws["J4"] = "Расход"
        ws["L4"] = "Сальдо на конец"
        ws["N4"] = "Sof Foyda"
        ws["F5"] = "Количество"
        ws["G5"] = "Сумма"
        ws["H5"] = "Количество"
        ws["I5"] = "Сумма"
        ws["J5"] = "Количество"
        ws["K5"] = "Сумма"
        ws["L5"] = "Количество"
        ws["M5"] = "Сумма"
        ws.merge_cells("N5:N6")
        ws["N5"] = "Сумма (Сумма $)"

        for r in range(4, 7):
            for c in range(1, 15):
                cell = ws.cell(r, c)
                cell.font = bold
                cell.alignment = center
                cell.border = border

        row = 7
        grand_open_qty = Decimal("0")
        grand_open_sum = Decimal("0")
        grand_in_qty = Decimal("0")
        grand_in_sum = Decimal("0")
        grand_out_qty = Decimal("0")
        grand_out_sum = Decimal("0")
        grand_out_sum_in_dollar = Decimal("0")
        grand_end_qty = Decimal("0")
        grand_end_sum = Decimal("0")
        grand_net_profit_uzs = Decimal("0")
        grand_net_profit_usd = Decimal("0")

        for category in categories:
            category_products = grouped_products.get(category.id, [])
            if not category_products:
                continue

            cat_open_qty = Decimal("0")
            cat_open_sum = Decimal("0")
            cat_in_qty = Decimal("0")
            cat_in_sum = Decimal("0")
            cat_out_qty = Decimal("0")
            cat_out_sum = Decimal("0")
            cat_out_sum_in_dollar = Decimal("0")
            cat_end_qty = Decimal("0")
            cat_end_sum = Decimal("0")
            cat_net_profit_uzs = Decimal("0")
            cat_net_profit_usd = Decimal("0")

            product_rows = []

            for product in category_products:
                open_in = open_in_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                open_out = open_out_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                in_period = in_map.get(product.id, {"qty": Decimal("0"), "total": Decimal("0")})
                out_period = out_map.get(product.id,
                                         {"qty": Decimal("0"), "total": Decimal("0"), "total_in_dollar": Decimal("0")})
                open_qty = open_in["qty"] - open_out["qty"]
                open_sum = open_in["total"] - open_cogs_map.get(product.id, Decimal("0"))
                in_qty = in_period["qty"]
                in_sum = in_period["total"]
                out_qty = out_period["qty"]
                out_sum = period_cogs_map.get(product.id, Decimal("0"))
                
                selling_price_uzs = out_period["total"]
                selling_price_usd = out_period["total_in_dollar"]
                cost_price_uzs = out_sum

                net_profit_uzs = selling_price_uzs - cost_price_uzs
                net_profit_usd = Decimal('0')
                if effective_rate > 0:
                    cost_price_usd = cost_price_uzs / effective_rate
                    net_profit_usd = selling_price_usd - cost_price_usd
                
                out_sum_in_dollar = out_period["total_in_dollar"]
                end_qty = open_qty + in_qty - out_qty
                end_sum = open_sum + in_sum - out_sum
                cat_open_qty += open_qty
                cat_open_sum += open_sum
                cat_in_qty += in_qty
                cat_in_sum += in_sum
                cat_out_qty += out_qty
                cat_out_sum += out_sum
                cat_out_sum_in_dollar += out_sum_in_dollar
                cat_end_qty += end_qty
                cat_end_sum += end_sum
                cat_net_profit_uzs += net_profit_uzs
                cat_net_profit_usd += net_profit_usd
                
                product_rows.append({
                    "code": product.id,
                    "name": product.name,
                    "unit": getattr(product, "unit", "дона"),
                    "open_qty": open_qty,
                    "open_sum": open_sum,
                    "in_qty": in_qty,
                    "in_sum": in_sum,
                    "out_qty": out_qty,
                    "out_sum": out_sum,
                    "out_sum_in_dollar": out_sum_in_dollar,
                    "end_qty": end_qty,
                    "end_sum": end_sum,
                    "net_profit_uzs": net_profit_uzs,
                    "net_profit_usd": net_profit_usd,
                })

            grand_open_qty += cat_open_qty
            grand_open_sum += cat_open_sum
            grand_in_qty += cat_in_qty
            grand_in_sum += cat_in_sum
            grand_out_qty += cat_out_qty
            grand_out_sum += cat_out_sum
            grand_out_sum_in_dollar += cat_out_sum_in_dollar
            grand_end_qty += cat_end_qty
            grand_end_sum += cat_end_sum
            grand_net_profit_uzs += cat_net_profit_uzs
            grand_net_profit_usd += cat_net_profit_usd
            
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
            ws.cell(row, 2, category.name)
            ws.cell(row, 2).font = bold
            ws.cell(row, 2).alignment = left
            money(ws.cell(row, 6), cat_open_qty)
            money(ws.cell(row, 7), cat_open_sum)
            money(ws.cell(row, 8), cat_in_qty)
            money(ws.cell(row, 9), cat_in_sum)
            money(ws.cell(row, 10), cat_out_qty)
            money_with_dollar(ws.cell(row, 11), cat_out_sum, cat_out_sum_in_dollar)
            money(ws.cell(row, 12), cat_end_qty)
            money(ws.cell(row, 13), cat_end_sum)
            money_with_dollar(ws.cell(row, 14), cat_net_profit_uzs, cat_net_profit_usd)

            for c in range(1, 15):
                ws.cell(row, c).border = border
                ws.cell(row, c).font = bold

            row += 1

            for item in product_rows:
                ws.cell(row, 1, item["code"])
                ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
                ws.cell(row, 2, item["name"])
                ws.cell(row, 5, item["unit"])
                money(ws.cell(row, 6), item["open_qty"])
                money(ws.cell(row, 7), item["open_sum"])
                money(ws.cell(row, 8), item["in_qty"])
                money(ws.cell(row, 9), item["in_sum"])
                money(ws.cell(row, 10), item["out_qty"])
                money_with_dollar(ws.cell(row, 11), item["out_sum"], item["out_sum_in_dollar"])
                money(ws.cell(row, 12), item["end_qty"])
                money(ws.cell(row, 13), item["end_sum"])
                money_with_dollar(ws.cell(row, 14), item["net_profit_uzs"], item["net_profit_usd"])

                for c in range(1, 15):
                    ws.cell(row, c).border = border
                    ws.cell(row, c).font = normal
                    ws.cell(row, c).alignment = left if c in [1, 2, 5] else right

                row += 1

        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        ws.cell(row, 1, "Жами:")
        ws.cell(row, 1).font = bold
        ws.cell(row, 1).alignment = right
        money(ws.cell(row, 6), grand_open_qty)
        money(ws.cell(row, 7), grand_open_sum)
        money(ws.cell(row, 8), grand_in_qty)
        money(ws.cell(row, 9), grand_in_sum)
        money(ws.cell(row, 10), grand_out_qty)
        money_with_dollar(ws.cell(row, 11), grand_out_sum, grand_out_sum_in_dollar)
        money(ws.cell(row, 12), grand_end_qty)
        money(ws.cell(row, 13), grand_end_sum)
        money_with_dollar(ws.cell(row, 14), grand_net_profit_uzs, grand_net_profit_usd)

        for c in range(1, 15):
            ws.cell(row, c).border = border
            ws.cell(row, c).font = bold

        widths = {"A": 12, "B": 42, "C": 2, "D": 2, "E": 10, "F": 12, "G": 18, "H": 12, "I": 18, "J": 12, "K": 18,
                  "L": 12, "M": 18, "N": 24}

        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output