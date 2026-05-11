from io import BytesIO
from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment
from openpyxl.utils import get_column_letter
from customer.models import Customer


class CustomerDebtExcelService:

    @staticmethod
    def _style(ws, last_row):

        thin = Side(style='thin', color='000000')
        border = Border(left=thin, right=thin, top=thin, bottom=thin)
        header_font = Font(bold=True, size=12)
        body_font = Font(size=12)
        center = Alignment(horizontal='center', vertical='center')
        right = Alignment(horizontal='right', vertical='center')
        left = Alignment(horizontal='left', vertical='center')

        widths = {
            1: 8,
            2: 45,
            3: 20,
            4: 20,
        }

        for col, width in widths.items():
            ws.column_dimensions[get_column_letter(col)].width = width

        for row in ws.iter_rows(min_row=1, max_row=last_row, min_col=1, max_col=4):
            for cell in row:
                cell.border = border
                cell.font = body_font

        for row in [1, 3]:
            for cell in ws[row]:
                cell.font = header_font
                cell.alignment = center

        for row in range(5, last_row + 1):
            ws.cell(row=row, column=1).alignment = center
            ws.cell(row=row, column=2).alignment = left
            ws.cell(row=row, column=3).alignment = right
            ws.cell(row=row, column=4).alignment = right
            ws.cell(row=row, column=3).number_format = '#,##0.00'
            ws.cell(row=row, column=4).number_format = '#,##0.00'

    @classmethod
    def build(cls):
        wb = Workbook()
        ws = wb.active
        today = timezone.localdate()
        ws.merge_cells('A1:D1')
        ws['A1'] = f'{today.strftime("%d.%m.%Y")}'
        ws['A3'] = '№'
        ws['B3'] = 'Mijozlar'
        ws['C3'] = 'Qarzdorlar'
        ws['D3'] = 'Ortiqcha to`lov qilganlar'
        row = 5
        total_dt = Decimal("0")
        total_kt = Decimal("0")
        customers = Customer.objects.all().order_by("full_name")
        for index, customer in enumerate(customers, start=1):
            customer.sync_debt()
            customer.refresh_from_db()
            debt = customer.debt or Decimal("0")
            dt = None
            kt = None

            if debt < 0:
                dt = abs(debt)
                total_dt += abs(debt)

            elif debt > 0:
                kt = debt
                total_kt += debt

            ws.cell(row=row, column=1, value=index)
            ws.cell(row=row, column=2, value=customer.full_name)
            ws.cell(row=row, column=3, value=float(kt) if kt else None)
            ws.cell(row=row, column=4, value=float(dt) if dt else None)

            row += 1

        ws.cell(row=row, column=2, value='Жами:')
        ws.cell(row=row, column=3, value=float(total_kt))
        ws.cell(row=row, column=4, value=float(total_dt))

        cls._style(ws, row)
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return output

    @classmethod
    def response(cls):
        output = cls.build()
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response['Content-Disposition'] = (
            'attachment; filename="customer_debt_report.xlsx"'
        )

        return response
