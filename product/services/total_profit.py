from decimal import Decimal


class TotalProfitService:

    @staticmethod
    def calculate(
            kromka_product_profit_som,
            kromka_product_profit_dollar,
            cutting_profit_som,
            cutting_profit_dollar,
            kromka_xizmat_profit_som,
            kromka_xizmat_profit_dollar,
            total_services_profit_som,
            total_services_profit_dollar,
    ):
        all_profit_som = (
                Decimal(str(kromka_product_profit_som))
                + Decimal(str(cutting_profit_som))
                + Decimal(str(kromka_xizmat_profit_som))
                + Decimal(str(total_services_profit_som))
        )

        all_profit_dollar = (
                Decimal(str(kromka_product_profit_dollar))
                + Decimal(str(cutting_profit_dollar))
                + Decimal(str(kromka_xizmat_profit_dollar))
                + Decimal(str(total_services_profit_dollar))
        )

        return {
            "all_profit_som": float(all_profit_som),
            "all_profit_dollar": float(all_profit_dollar),
        }
