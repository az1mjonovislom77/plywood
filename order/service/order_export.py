from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from io import BytesIO


def generate_statement_excel(customer, transactions):
    wb = Workbook()
    ws = wb.active
    bold = Font(bold=True, size=12)
    normal = Font(size=11)

    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    number_format = "#,##0"

    def set_money(cell, value):
        cell.value = value
        cell.number_format = number_format

    row = 1

    ws["A1"] = "01.04.2026 00:00:00"
    ws["A2"] = "24.04.2026 23:59:59"
    ws["A4"] = customer.full_name
    ws["A4"].font = bold

    row = 6

    ws.merge_cells(start_row=row, start_column=1, end_row=row + 1, end_column=1)
    ws.merge_cells(start_row=row, start_column=2, end_row=row + 1, end_column=2)
    ws.merge_cells(start_row=row, start_column=3, end_row=row + 1, end_column=3)
    ws.merge_cells(start_row=row, start_column=4, end_row=row + 1, end_column=4)
    ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=6)
    ws.merge_cells(start_row=row, start_column=7, end_row=row, end_column=8)
    ws.merge_cells(start_row=row, start_column=9, end_row=row + 1, end_column=9)

    ws["A6"] = "№"
    ws["B6"] = "Дата"
    ws["C6"] = "Регистратор"
    ws["D6"] = "Товар"
    ws["E6"] = "Приход"
    ws["G6"] = "Расход"
    ws["I6"] = "Остаток"
    ws["E7"] = "Кол"
    ws["F7"] = "Сумма"
    ws["G7"] = "Кол"
    ws["H7"] = "Сумма"

    for r in range(6, 8):
        for c in range(1, 10):
            cell = ws.cell(row=r, column=c)
            cell.font = bold
            cell.alignment = center
            cell.border = border

    row = 8
    balance = 0

    for i, t in enumerate(transactions, start=1):
        ws.cell(row=row, column=1, value=i)
        ws.cell(row=row, column=2, value=t["date"])
        ws.cell(row=row, column=3, value=t["doc"])
        ws.cell(row=row, column=4, value=t["product"])

        if t["type"] == "in":
            ws.cell(row=row, column=5, value=t["qty"])
            set_money(ws.cell(row=row, column=6), t["amount"])
            balance += t["amount"]

        else:
            ws.cell(row=row, column=7, value=t["qty"])
            set_money(ws.cell(row=row, column=8), t["amount"])
            balance -= t["amount"]

        set_money(ws.cell(row=row, column=9), balance)

        for c in range(1, 10):
            ws.cell(row=row, column=c).border = border

        row += 1

    ws.cell(row=row, column=4, value="Жами:").font = bold
    set_money(ws.cell(row=row, column=8), sum(t["amount"] for t in transactions))

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 15
    ws.column_dimensions["C"].width = 35
    ws.column_dimensions["D"].width = 35
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 15
    ws.column_dimensions["G"].width = 10
    ws.column_dimensions["H"].width = 15
    ws.column_dimensions["I"].width = 15

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer
