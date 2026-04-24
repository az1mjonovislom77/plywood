from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO


def generate_order_excel(order):
    wb = Workbook()
    ws = wb.active

    title_font = Font(size=18, bold=True)
    header_font = Font(size=12, bold=True)
    normal_font = Font(size=12)

    center = Alignment(horizontal="center", vertical="center")
    left = Alignment(horizontal="left", vertical="center")

    border = Border(
        left=Side(style="medium"),
        right=Side(style="medium"),
        top=Side(style="medium"),
        bottom=Side(style="medium"),
    )

    number_format = '#,##0'

    def set_money(cell, value):
        cell.value = value
        cell.number_format = number_format
        cell.font = normal_font

    row = 1

    ws.merge_cells("A1:D1")
    cell = ws["A1"]
    cell.value = f"BUYURTMA #{order.id}"
    cell.font = title_font
    cell.alignment = center

    ws.row_dimensions[1].height = 30
    row += 2

    ws["A3"] = "Mijoz:"
    ws["A3"].font = header_font
    ws["B3"] = order.customer.full_name if order.customer else "Anonim"
    ws["B3"].font = normal_font

    row = 5

    headers = ["Mahsulot", "Narx", "Miqdor", "Jami"]

    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    ws.row_dimensions[row].height = 25
    row += 1

    for item in order.items.select_related("product"):
        name = item.product.name

        size = getattr(item.product, "size", "")
        thickness = getattr(item.product, "thickness", "")
        full_name = f"{name} {size} {thickness}".strip()

        price = float(item.price)
        qty = float(item.quantity)
        jami = price * qty

        cell = ws.cell(row=row, column=1, value=full_name)
        cell.font = normal_font
        cell.alignment = left
        cell.border = border
        cell = ws.cell(row=row, column=2)
        set_money(cell, price)
        cell.alignment = center
        cell.border = border
        cell = ws.cell(row=row, column=3, value=qty)
        cell.font = normal_font
        cell.alignment = center
        cell.border = border
        cell = ws.cell(row=row, column=4)
        set_money(cell, jami)
        cell.alignment = center
        cell.border = border

        ws.row_dimensions[row].height = 22
        row += 1

        if item.banding:
            b = item.banding
            length = float(b.length)
            price_per_m = float(b.thickness.price) if b.thickness else 0
            jami_b = length * price_per_m

            ws.cell(row=row, column=1, value=f"Kromka: {length}m x {price_per_m}")
            set_money(ws.cell(row=row, column=4), jami_b)
            row += 1

        if item.cutting:
            c = item.cutting
            count = float(c.count)
            price_c = float(c.price)
            jami_c = count * price_c

            ws.cell(row=row, column=1, value=f"Kesish: {count} x {price_c}")
            set_money(ws.cell(row=row, column=4), jami_c)
            row += 1

    row += 2

    total_price = float(order.total_price)
    paid = float(order.covered_amount)
    remaining = max(total_price - paid, 0)

    def total_row(label, value, bold_text=False):
        nonlocal row
        ws.cell(row=row, column=3, value=label).font = header_font
        cell = ws.cell(row=row, column=4)
        set_money(cell, value)
        if bold_text:
            cell.font = header_font
        row += 1

    total_row("Jami summa", total_price, True)
    total_row("To'langan", paid)
    total_row("Qoldiq", remaining)

    ws.cell(row=row, column=3, value="To'lov turi").font = header_font
    ws.cell(row=row, column=4, value=order.get_payment_method_display()).font = normal_font
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 15
    ws.column_dimensions["D"].width = 20

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer
