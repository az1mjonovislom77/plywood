from decimal import Decimal

from django.db.models import Sum, F, Value, DecimalField
from django.db.models.functions import Coalesce

from category.models import Category
from order.models import OrderItem
from product.services.export_json import MaterialReportJsonService
from product.services.material_profit import KROMKA_CATEGORY_NAME, MaterialProfitService
from utils.models import Services, ServicesName
from utils.service.comprehensive_stats import DashboardStatsService


class AncillaryProfitService:
    @staticmethod
    def money_field():
        return DecimalField(max_digits=18, decimal_places=2)

    @classmethod
    def _som_to_dollar(cls, amount_som: Decimal, rate_value: Decimal) -> Decimal:
        if rate_value and rate_value != Decimal("0"):
            return (amount_som / rate_value).quantize(Decimal("0.01"))
        return Decimal("0")

    @classmethod
    def calc_cutting_profit(cls, date_from, date_to, rate_value: Decimal):
        stats = DashboardStatsService.get_stats(date_from, date_to)
        cutting_som = Decimal(str(stats.get("cutting_sales", 0)))
        cutting_dollar = cls._som_to_dollar(cutting_som, rate_value)
        return cutting_som, cutting_dollar

    @classmethod
    def calc_banding_profit(cls, start_dt, end_dt, rate_value: Decimal):
        kromka = Category.objects.filter(name__iexact=KROMKA_CATEGORY_NAME).first()
        if not kromka:
            return Decimal("0"), Decimal("0")

        banding_qs = OrderItem.objects.filter(
            MaterialReportJsonService._accepted_order_filter(),
            MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt),
            product__category=kromka,
            banding__isnull=False,
        ).aggregate(
            banding_som=Coalesce(
                Sum(
                    F("banding__length") * F("banding__thickness")
                    - Coalesce(F("banding__discount"), Value(Decimal("0")))
                ),
                Value(Decimal("0")),
                output_field=cls.money_field(),
            )
        )
        banding_som = Decimal(str(banding_qs.get("banding_som") or 0))
        banding_dollar = cls._som_to_dollar(banding_som, rate_value)
        return banding_som, banding_dollar

    @classmethod
    def calc_services_profit(cls, start_dt, end_dt, rate_value: Decimal):
        services_som = Decimal("0")
        services_dollar = Decimal("0")
        services_stats = []

        for service_name in ServicesName.objects.all():
            service_total_som = Services.objects.filter(
                services_name=service_name,
                created_at__gte=start_dt,
                created_at__lt=end_dt,
            ).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0")),
                    output_field=cls.money_field(),
                )
            )["total"]
            service_total_som = Decimal(str(service_total_som or 0))
            service_total_dollar = cls._som_to_dollar(service_total_som, rate_value)
            services_stats.append({
                "service_name": service_name.name,
                "profit_som": float(service_total_som),
                "profit_dollar": float(service_total_dollar),
            })
            services_som += service_total_som
            services_dollar += service_total_dollar

        return services_som, services_dollar, services_stats

    @classmethod
    def calc_all_ancillary(cls, date_from, date_to, start_dt, end_dt, end_date):
        rate_value = MaterialProfitService.get_rate_for_date(end_date)
        cutting_som, cutting_dollar = cls.calc_cutting_profit(date_from, date_to, rate_value)
        banding_som, banding_dollar = cls.calc_banding_profit(start_dt, end_dt, rate_value)
        services_som, services_dollar, services_stats = cls.calc_services_profit(
            start_dt, end_dt, rate_value
        )
        return {
            "rate_value": rate_value,
            "cutting_som": cutting_som,
            "cutting_dollar": cutting_dollar,
            "banding_som": banding_som,
            "banding_dollar": banding_dollar,
            "services_som": services_som,
            "services_dollar": services_dollar,
            "services_stats": services_stats,
        }
