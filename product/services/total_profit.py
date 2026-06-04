from product.services.ancillary_profit import AncillaryProfitService
from product.services.material_profit import MaterialProfitService


class AllProfitService:

    @classmethod
    def calculate(cls, date_from, date_to, start_dt, end_dt, end_date, context=None):
        if context is None:
            context = MaterialProfitService.build_profit_context(date_from, date_to)
        else:
            start_dt = context["start_dt"]
            end_dt = context["end_dt"]
            end_date = context["end_date"]
        material_som, material_dollar = MaterialProfitService.calc_grand_total(context)
        ancillary = AncillaryProfitService.calc_all_ancillary(
            date_from, date_to, start_dt, end_dt, end_date
        )

        all_profit_som = (
            material_som
            + ancillary["cutting_som"]
            + ancillary["banding_som"]
            + ancillary["services_som"]
        )
        all_profit_dollar = (
            material_dollar
            + ancillary["cutting_dollar"]
            + ancillary["banding_dollar"]
            + ancillary["services_dollar"]
        )

        return {
            "all_profit_som": float(all_profit_som),
            "all_profit_dollar": float(all_profit_dollar),
        }
