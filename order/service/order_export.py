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

    def set_money(cell, value):
        cell.value = float(value)
        cell.number_format = number_format

    customer = order.customer
    ws["A4"] = customer.full_name if customer else "Anonim"
    ws["A4"].font = bold

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
    ws["D6"] = "Тўлов"
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
    index = 1

    balance = float(customer.debt) if customer else 0

    ws.cell(row=row, column=1, value=index)
    ws.cell(row=row, column=5, value="Boshlang‘ich balans")
    set_money(ws.cell(row=row, column=10), balance)

    for c in range(1, 11):
        ws.cell(row=row, column=c).border = border

    row += 1
    index += 1

    if order.covered_amount:
        amount = float(order.covered_amount)

        ws.cell(row=row, column=1, value=index)
        ws.cell(row=row, column=2, value=str(order.created_at.date()))
        ws.cell(row=row, column=5, value="To‘lov")
        set_money(ws.cell(row=row, column=7), amount)

        balance += amount
        set_money(ws.cell(row=row, column=10), balance)

        for c in range(1, 11):
            ws.cell(row=row, column=c).border = border

        row += 1
        index += 1

    for item in order.items.select_related("product"):
        qty = float(item.quantity)
        amount = float(item.price) * qty

        ws.cell(row=row, column=1, value=index)
        ws.cell(row=row, column=2, value=str(order.created_at.date()))
        ws.cell(row=row, column=3, value=f"Order #{order.id}")
        ws.cell(row=row, column=4, value=order.get_payment_method_display())
        ws.cell(row=row, column=5, value=item.product.name)

        ws.cell(row=row, column=8, value=qty)
        set_money(ws.cell(row=row, column=9), amount)

        balance -= amount
        set_money(ws.cell(row=row, column=10), balance)

        for c in range(1, 11):
            ws.cell(row=row, column=c).border = border

        row += 1
        index += 1

    ws.cell(row=row, column=5, value="Жами:").font = bold
    set_money(ws.cell(row=row, column=9), float(order.total_price))

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 15
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