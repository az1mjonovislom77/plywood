from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO


def generate_order_ledger_excel(order):
    wb = Workbook()
    ws = wb.active

    bold = Font(bold=True, size=11)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    number_format = "#,##0"

    def money(cell, val):
        cell.value = float(val)
        cell.number_format = number_format

    ws["A1"] = str(order.created_at)
    ws["A2"] = str(order.created_at)
    ws["A4"] = order.customer.full_name if order.customer else ""

    balance = float(order.customer.debt) if order.customer else 0

    ws.merge_cells("I4:J4")
    ws["I4"] = "Остаток"
    ws["I4"].font = bold
    ws["I4"].alignment = center
    ws["J4"] = balance
    ws["J4"].number_format = number_format
    ws["J4"].font = bold
    ws["J4"].alignment = center

    ws.merge_cells("A6:A7")
    ws.merge_cells("B6:B7")
    ws.merge_cells("C6:C7")
    ws.merge_cells("D6:D7")
    ws.merge_cells("E6:E7")
    ws.merge_cells("F6:G6")
    ws.merge_cells("H6:I6")
    ws.merge_cells("J6:J7")

    ws["A6"] = "№"
    ws["B6"] = "Дата"
    ws["C6"] = "Регистратор"
    ws["D6"] = "Вид оплаты"
    ws["E6"] = "Товар"

    ws["F6"] = "Приход"
    ws["H6"] = "Расход"
    ws["J6"] = "Остаток"

    ws["F7"] = "Кол"
    ws["G7"] = "Сумма"
    ws["H7"] = "Кол"
    ws["I7"] = "Сумма"

    for r in range(6, 8):
        for c in range(1, 11):
            cell = ws.cell(row=r, column=c)
            cell.font = bold
            cell.alignment = center
            cell.border = border

    row = 8
    i = 1

    for item in order.items.select_related("product", "banding", "cutting"):
        qty = float(item.quantity)
        amount = float(item.price) * qty

        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=str(order.created_at.date()))
        ws.cell(row=row, column=3, value=f"Продажа товара {order.id}")
        ws.cell(row=row, column=4, value=order.get_payment_method_display())
        ws.cell(row=row, column=5, value=item.product.name)

        ws.cell(row=row, column=8, value=qty)
        money(ws.cell(row=row, column=9), amount)

        balance -= amount
        money(ws.cell(row=row, column=10), balance)

        for c in range(1, 11):
            ws.cell(row=row, column=c).border = border

        row += 1
        i += 1

        if item.banding:
            b = item.banding
            total = float(b.length) * float(b.thickness.price if b.thickness else 0)

            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=5, value=f"Кромка {b.length}м")
            ws.cell(row=row, column=8, value=float(b.length))
            money(ws.cell(row=row, column=9), total)

            balance -= total
            money(ws.cell(row=row, column=10), balance)

            for c in range(1, 11):
                ws.cell(row=row, column=c).border = border

            row += 1
            i += 1

        if item.cutting:
            c = item.cutting
            total = float(c.count) * float(c.price)

            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=5, value="Хизмат (Распил)")
            ws.cell(row=row, column=8, value=float(c.count))
            money(ws.cell(row=row, column=9), total)

            balance -= total
            money(ws.cell(row=row, column=10), balance)

            for c in range(1, 11):
                ws.cell(row=row, column=c).border = border

            row += 1
            i += 1

    ws.cell(row=row, column=4, value="Жами:").font = bold
    money(ws.cell(row=row, column=9), float(order.total_price))

    row += 2

    paid = float(order.covered_amount)
    final_balance = balance + paid

    ws.cell(row=row, column=8, value="To‘langan").font = bold
    money(ws.cell(row=row, column=9), paid)

    row += 1

    ws.cell(row=row, column=8, value="Qoldiq").font = bold
    money(ws.cell(row=row, column=9), final_balance)

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 35
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 40
    ws.column_dimensions["F"].width = 10
    ws.column_dimensions["G"].width = 15
    ws.column_dimensions["H"].width = 10
    ws.column_dimensions["I"].width = 15
    ws.column_dimensions["J"].width = 18

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer