from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField, Case, When
from django.db.models.functions import Coalesce
from acceptance.models import CurrencyRate
from category.models import Category
from order.models import OrderItem
from utils.models import Services, ServicesName
from product.services.export_json import MaterialReportJsonService
from utils.service.comprehensive_stats import DashboardStatsService


class AllProfitService:

    @classmethod
    def calculate(cls, date_from, date_to, start_dt, end_dt, end_date):
        rate_obj = CurrencyRate.objects.filter(date__lte=end_date).order_by("-date").first()
        rate_value = (Decimal(str(rate_obj.rate))
                      if rate_obj
                      else Decimal("0"))

        out_revenue_qs = (
            OrderItem.objects.filter(MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt))
            .values("product_id")
            .annotate(
                out_revenue_in_dollar=Coalesce(
                    Sum(F("quantity") * Case(
                        When(new_price_in_dollar__isnull=False, then=F("new_price_in_dollar")),
                        default=F("price_in_dollar"),
                        output_field=DecimalField(max_digits=18, decimal_places=4))),
                    Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=4),
                )
            )
        )

        out_revenue_map = {
            r["product_id"]: Decimal(str(r.get("out_revenue_in_dollar") or 0))
            for r in out_revenue_qs
        }

        (
            _,
            period_cogs_map,
            _,
            period_cogs_map_in_dollar,
        ) = MaterialReportJsonService._calc_fifo(
            start_dt,
            end_dt,
            end_date,
        )

        category_profit_som = Decimal("0")
        category_profit_dollar = Decimal("0")

        categories = Category.objects.exclude(name__iexact="KROMKA")

        for category in categories:
            for product in category.products.all():
                pid = product.id
                revenue = out_revenue_map.get(pid, Decimal("0"))
                cogs = (period_cogs_map_in_dollar.get(pid, Decimal("0")))
                profit_dollar = revenue - cogs
                profit_som = (profit_dollar * rate_value).quantize(Decimal("0.01"))
                category_profit_dollar += (profit_dollar)
                category_profit_som += (profit_som)
        kromka = Category.objects.filter(name__iexact="KROMKA").first()
        kromka_profit_som = Decimal("0")
        kromka_profit_dollar = Decimal("0")

        if kromka:
            for product in kromka.products.all():
                pid = product.id
                revenue = out_revenue_map.get(pid, Decimal("0"))
                cogs = (period_cogs_map_in_dollar.get(pid, Decimal("0")))
                profit_dollar = revenue - cogs
                profit_som = (profit_dollar * rate_value).quantize(Decimal("0.01"))
                kromka_profit_dollar += (profit_dollar)
                kromka_profit_som += (profit_som)

        stats = DashboardStatsService.get_stats(date_from, date_to, )
        cutting_som = Decimal(str(stats.get("cutting_sales", 0)))
        cutting_dollar = Decimal("0")

        if rate_value:
            cutting_dollar = (cutting_som / rate_value).quantize(Decimal("0.01"))
        banding_qs = OrderItem.objects.filter(
            MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt),
            product__category=kromka, banding__isnull=False,
        ).aggregate(
            banding_som=Coalesce(
                Sum(
                    F("banding__length") * F("banding__thickness")
                    - Coalesce(F("banding__discount"), Value(Decimal("0")))),
                Value(Decimal("0")), output_field=DecimalField()))

        banding_som = Decimal(str(banding_qs.get("banding_som") or 0))
        banding_dollar = Decimal("0")

        if rate_value:
            banding_dollar = (banding_som / rate_value).quantize(Decimal("0.01"))
        services_som = Decimal("0")
        services_dollar = Decimal("0")
        for service_name in ServicesName.objects.all():
            total = Services.objects.filter(
                services_name=service_name, created_at__gte=start_dt, created_at__lt=end_dt,
            ).aggregate(
                total=Coalesce(Sum("total_price"), Value(Decimal("0")), output_field=DecimalField()))["total"]

            total = Decimal(str(total))
            services_som += total

            if rate_value:
                services_dollar += (total / rate_value).quantize(Decimal("0.01"))

        all_profit_som = (
                category_profit_som
                + kromka_profit_som
                + cutting_som
                + banding_som
                + services_som
        )

        all_profit_dollar = (
                category_profit_dollar
                + kromka_profit_dollar
                + cutting_dollar
                + banding_dollar
                + services_dollar
        )

        return {
            "all_profit_som": float(all_profit_som),
            "all_profit_dollar": float(all_profit_dollar),
        }
