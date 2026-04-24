from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO


def generate_order_excel(order):
    wb = Workbook()
    ws = wb.active

    bold = Font(bold=True)
    center = Alignment(horizontal="center")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    row = 1

    ws[f"A{row}"] = f"Buyurtma #{order.id}"
    ws[f"A{row}"].font = Font(size=14, bold=True)
    row += 2

    ws[f"A{row}"] = "Mijoz:"
    ws[f"B{row}"] = order.customer.full_name if order.customer else "Anonim"
    row += 2

    headers = ["Mahsulot", "Narx", "Miqdor", "Jami"]
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = bold
        cell.alignment = center
        cell.border = border

    row += 1

    total = 0

    for item in order.items.select_related("product"):
        name = item.product.name

        size = getattr(item.product, "size", "")
        thickness = getattr(item.product, "thickness", "")
        full_name = f"{name} {size} {thickness}".strip()

        price = float(item.price)
        qty = float(item.quantity)
        jami = price * qty
        total += jami

        data = [full_name, price, qty, jami]

        for col, val in enumerate(data, start=1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.border = border

        row += 1

        if item.banding:
            b = item.banding
            length = float(b.length)
            price_per_m = float(b.thickness.price) if b.thickness else 0
            jami_b = length * price_per_m

            ws.cell(row=row, column=1, value=f"Kromka: {length}m x {price_per_m}")
            ws.cell(row=row, column=4, value=jami_b)

            total += jami_b
            row += 1

        if item.cutting:
            c = item.cutting
            count = float(c.count)
            price_c = float(c.price)
            jami_c = count * price_c

            ws.cell(row=row, column=1, value=f"Kesish: {count} x {price_c}")
            ws.cell(row=row, column=4, value=jami_c)

            total += jami_c
            row += 1

    if order.banding:
        b = order.banding
        length = float(b.length)
        price_per_m = float(b.thickness.price) if b.thickness else 0
        jami_b = length * price_per_m

        ws.cell(row=row, column=1, value=f"Kromka: {length}m x {price_per_m}")
        ws.cell(row=row, column=4, value=jami_b)

        total += jami_b
        row += 1

    if order.cutting:
        c = order.cutting
        count = float(c.count)
        price_c = float(c.price)
        jami_c = count * price_c

        ws.cell(row=row, column=1, value=f"Kesish: {count} x {price_c}")
        ws.cell(row=row, column=4, value=jami_c)

        total += jami_c
        row += 1

    row += 1

    total_price = float(order.total_price)
    paid = float(order.covered_amount)
    remaining = max(total_price - paid, 0)

    ws.cell(row=row, column=3, value="Jami summa").font = bold
    ws.cell(row=row, column=4, value=total_price).font = bold

    row += 1
    ws.cell(row=row, column=3, value="To'langan")
    ws.cell(row=row, column=4, value=paid)
    row += 1
    ws.cell(row=row, column=3, value="Qoldiq")
    ws.cell(row=row, column=4, value=remaining)
    row += 1
    ws.cell(row=row, column=3, value="To'lov turi")
    ws.cell(row=row, column=4, value=order.payment_method)

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter

        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[col_letter].width = max_length + 2

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer