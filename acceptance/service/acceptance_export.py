import openpyxl
from openpyxl.styles import Font, Alignment


class AcceptanceExportService:

    @staticmethod
    def build_supplier_excel(queryset, supplier_name, date):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Acceptance"

        title = f"{supplier_name} - {date.strftime('%d.%m.%Y')}"
        ws.merge_cells("A1:D1")
        ws["A1"] = title
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = Alignment(horizontal="center")

        headers = ["Mahsulot", "Miqdor", "Kelish narxi", "Investitsiya"]
        ws.append([])
        ws.append(headers)

        for cell in ws[3]:
            cell.font = Font(bold=True)

        total_quantity = 0
        total_investment = 0

        for obj in queryset:
            investment = obj.arrival_price * obj.count

            ws.append([
                obj.product.name,
                float(obj.count),
                float(obj.arrival_price),
                float(investment),
            ])

            total_quantity += obj.count
            total_investment += investment

        ws.append([])
        ws.append(["JAMI", float(total_quantity), "", float(total_investment)])

        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)

        ws.column_dimensions["A"].width = 40
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 20

        return wb
