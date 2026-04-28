from io import BytesIO
from decimal import Decimal

from django.db.models import Sum, Value, DecimalField, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_date

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

from category.models import Category
from product.models import Product
from acceptance.models import Acceptance
from order.models import OrderItem


class MaterialReportService:
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

    @classmethod
    def build_excel(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = cls._parse_bounds(date_from, date_to)

        categories = list(Category.objects.all().order_by("name"))
        products = list(Product.objects.select_related("category").order_by("category__name", "name"))

        open_in_map = cls._to_map(
            Acceptance.objects.filter(
                acceptance_status="accept",
                created_at__lt=start_dt,
            ).values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("count") * F("arrival_price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        open_out_map = cls._to_map(
            OrderItem.objects.filter(
                order__created_at__lt=start_dt
            ).values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("quantity") * F("price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        in_map = cls._to_map(
            Acceptance.objects.filter(
                acceptance_status="accept",
                created_at__gte=start_dt,
                created_at__lt=end_dt,
            ).values("product_id").annotate(
                qty=Coalesce(Sum("count"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("count") * F("arrival_price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

        out_map = cls._to_map(
            OrderItem.objects.filter(
                order__created_at__gte=start_dt,
                order__created_at__lt=end_dt,
            ).values("product_id").annotate(
                qty=Coalesce(Sum("quantity"), Value(Decimal("0")), output_field=DecimalField()),
                total=Coalesce(Sum(F("quantity") * F("price")), Value(Decimal("0")), output_field=DecimalField()),
            )
        )

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
            cell.value = float(value or 0)
            cell.number_format = "#,##0.000"

        ws.merge_cells("B1:L1")
        ws["B1"] = f"Материальный отчет за {start_date.strftime('%B %Y')} г. - {end_date.strftime('%B %Y')} г."
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

        ws["F5"] = "Количество"
        ws["G5"] = "Сумма"
        ws["H5"] = "Количество"
        ws["I5"] = "Сумма"
        ws["J5"] = "Количество"
        ws["K5"] = "Сумма"
        ws["L5"] = "Количество"
        ws["M5"] = "Сумма"

        for r in range(4, 7):
            for c in range(1, 14):
                cell = ws.cell(r, c)
                cell.font = bold
                cell.alignment = center
                cell.border = border

        row = 7

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
            cat_end_qty = Decimal("0")
            cat_end_sum = Decimal("0")

            product_rows = []

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

                cat_open_qty += open_qty
                cat_open_sum += open_sum
                cat_in_qty += in_qty
                cat_in_sum += in_sum
                cat_out_qty += out_qty
                cat_out_sum += out_sum
                cat_end_qty += end_qty
                cat_end_sum += end_sum

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
                    "end_qty": end_qty,
                    "end_sum": end_sum,
                })

            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=4)
            ws.cell(row, 2, category.name)
            ws.cell(row, 2).font = bold
            ws.cell(row, 2).alignment = left

            money(ws.cell(row, 6), cat_open_qty)
            money(ws.cell(row, 7), cat_open_sum)
            money(ws.cell(row, 8), cat_in_qty)
            money(ws.cell(row, 9), cat_in_sum)
            money(ws.cell(row, 10), cat_out_qty)
            money(ws.cell(row, 11), cat_out_sum)
            money(ws.cell(row, 12), cat_end_qty)
            money(ws.cell(row, 13), cat_end_sum)

            for c in range(1, 14):
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
                money(ws.cell(row, 11), item["out_sum"])
                money(ws.cell(row, 12), item["end_qty"])
                money(ws.cell(row, 13), item["end_sum"])

                for c in range(1, 14):
                    ws.cell(row, c).border = border
                    ws.cell(row, c).font = normal
                    ws.cell(row, c).alignment = left if c in [1, 2, 5] else right

                row += 1

        widths = {
            "A": 12,
            "B": 42,
            "C": 2,
            "D": 2,
            "E": 10,
            "F": 12,
            "G": 18,
            "H": 12,
            "I": 18,
            "J": 12,
            "K": 18,
            "L": 12,
            "M": 18,
        }

        for col, width in widths.items():
            ws.column_dimensions[col].width = width

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output