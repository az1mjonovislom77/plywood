from decimal import Decimal

from django.db.models import Sum, F, Value, DecimalField, ExpressionWrapper, Case, When
from django.db.models.functions import Coalesce

from acceptance.models import CurrencyRate
from category.models import Category
from order.models import OrderItem
from product.models import Product
from product.services.export_json import MaterialReportJsonService

KROMKA_CATEGORY_NAME = "KROMKA"


def is_kromka_category(category) -> bool:
    return category.name.strip().upper() == KROMKA_CATEGORY_NAME


class MaterialProfitService:
    @staticmethod
    def money_field():
        return DecimalField(max_digits=18, decimal_places=2)

    @classmethod
    def money_expr(cls, left, right):
        return ExpressionWrapper(F(left) * F(right), output_field=cls.money_field())

    @classmethod
    def get_rate_for_date(cls, end_date) -> Decimal:
        rate_obj = CurrencyRate.objects.filter(date__lte=end_date).order_by("-date").first()
        return Decimal(str(rate_obj.rate)) if rate_obj else Decimal("0")

    @classmethod
    def build_period_revenue_maps(cls, start_dt, end_dt):
        rows = (
            OrderItem.objects.filter(
                MaterialReportJsonService._accepted_order_filter(),
                MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt),
            )
            .values("product_id")
            .annotate(
                out_revenue_som=Coalesce(
                    Sum(cls.money_expr("quantity", "price")),
                    Value(Decimal("0")),
                    output_field=cls.money_field(),
                ),
                out_revenue_in_dollar=Coalesce(
                    Sum(
                        F("quantity")
                        * Case(
                            When(new_price_in_dollar__isnull=False, then=F("new_price_in_dollar")),
                            default=F("price_in_dollar"),
                            output_field=cls.money_field(),
                        )
                    ),
                    Value(Decimal("0")),
                    output_field=cls.money_field(),
                ),
            )
        )
        revenue_som_map = {}
        revenue_dollar_map = {}
        for row in rows:
            pid = row["product_id"]
            revenue_som_map[pid] = Decimal(str(row.get("out_revenue_som") or 0))
            revenue_dollar_map[pid] = Decimal(str(row.get("out_revenue_in_dollar") or 0))
        return revenue_som_map, revenue_dollar_map

    @classmethod
    def calc_product_profit(
        cls,
        revenue_dollar: Decimal,
        revenue_som: Decimal,
        cogs_dollar: Decimal,
        cogs_som: Decimal,
        rate_value: Decimal,
    ):
        profit_dollar = revenue_dollar - cogs_dollar
        if rate_value and rate_value != Decimal("0"):
            profit_som = (profit_dollar * rate_value).quantize(Decimal("0.01"))
        else:
            profit_som = revenue_som - cogs_som
        return profit_som, profit_dollar

    @classmethod
    def build_profit_context(cls, date_from=None, date_to=None):
        start_date, end_date, start_dt, end_dt = MaterialReportJsonService._parse_bounds(
            date_from, date_to
        )
        revenue_som_map, revenue_dollar_map = cls.build_period_revenue_maps(start_dt, end_dt)
        (
            open_cogs_map,
            period_cogs_map,
            open_cogs_map_in_dollar,
            period_cogs_map_in_dollar,
        ) = MaterialReportJsonService._calc_fifo(start_dt, end_dt, end_date)
        rate_value = cls.get_rate_for_date(end_date)
        return {
            "start_date": start_date,
            "end_date": end_date,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "revenue_som_map": revenue_som_map,
            "revenue_dollar_map": revenue_dollar_map,
            "open_cogs_map": open_cogs_map,
            "period_cogs_map": period_cogs_map,
            "open_cogs_map_in_dollar": open_cogs_map_in_dollar,
            "period_cogs_map_in_dollar": period_cogs_map_in_dollar,
            "rate_value": rate_value,
        }

    @classmethod
    def _product_profit_from_context(cls, product_id, context):
        revenue_dollar = context["revenue_dollar_map"].get(product_id, Decimal("0"))
        revenue_som = context["revenue_som_map"].get(product_id, Decimal("0"))
        cogs_dollar = context["period_cogs_map_in_dollar"].get(product_id, Decimal("0"))
        cogs_som = context["period_cogs_map"].get(product_id, Decimal("0"))
        return cls.calc_product_profit(
            revenue_dollar,
            revenue_som,
            cogs_dollar,
            cogs_som,
            context["rate_value"],
        )

    @classmethod
    def calc_category_profit(cls, category, context):
        cat_profit_som = Decimal("0")
        cat_profit_dollar = Decimal("0")
        for product in category.products.all():
            profit_som, profit_dollar = cls._product_profit_from_context(product.id, context)
            cat_profit_som += profit_som
            cat_profit_dollar += profit_dollar
        return cat_profit_som, cat_profit_dollar

    @classmethod
    def calc_profits_by_category(cls, context, *, exclude_kromka=False, only_kromka=False):
        categories = list(Category.objects.prefetch_related("products").order_by("name"))
        result_categories = []
        total_profit_som = Decimal("0")
        total_profit_dollar = Decimal("0")
        products_count = 0

        for category in categories:
            kromka = is_kromka_category(category)
            if exclude_kromka and kromka:
                continue
            if only_kromka and not kromka:
                continue

            products = category.products.all()
            if exclude_kromka or only_kromka:
                products_count += products.count()

            cat_profit_som, cat_profit_dollar = cls.calc_category_profit(category, context)
            total_profit_som += cat_profit_som
            total_profit_dollar += cat_profit_dollar

            result_categories.append({
                "id": category.id,
                "name": category.name,
                "profit_som": float(cat_profit_som),
                "profit_dollar": float(cat_profit_dollar),
            })

        return {
            "categories": result_categories,
            "total_profit_som": total_profit_som,
            "total_profit_dollar": total_profit_dollar,
            "products_count": products_count,
        }

    @classmethod
    def calc_grand_total(cls, context, *, exclude_kromka=False):
        categories = Category.objects.prefetch_related("products").order_by("name")
        grand_profit_som = Decimal("0")
        grand_profit_dollar = Decimal("0")

        for category in categories:
            if exclude_kromka and is_kromka_category(category):
                continue
            products = list(
                Product.objects.filter(category=category).order_by("name")
            )
            if not products:
                continue
            for product in products:
                profit_som, profit_dollar = cls._product_profit_from_context(product.id, context)
                grand_profit_som += profit_som
                grand_profit_dollar += profit_dollar

        return grand_profit_som, grand_profit_dollar

    @classmethod
    def calc_kromka_product_profit(cls, context):
        kromka = Category.objects.prefetch_related("products").filter(name__iexact=KROMKA_CATEGORY_NAME).first()
        if not kromka:
            return Decimal("0"), Decimal("0"), 0
        profit_som, profit_dollar = cls.calc_category_profit(kromka, context)
        return profit_som, profit_dollar, kromka.products.count()

    @classmethod
    def product_profit_row(cls, product, context):
        profit_som, profit_dollar = cls._product_profit_from_context(product.id, context)
        revenue_som = context["revenue_som_map"].get(product.id, Decimal("0"))
        revenue_dollar = context["revenue_dollar_map"].get(product.id, Decimal("0"))
        cogs_som = context["period_cogs_map"].get(product.id, Decimal("0"))
        cogs_dollar = context["period_cogs_map_in_dollar"].get(product.id, Decimal("0"))
        return {
            "profit_som": profit_som,
            "profit_dollar": profit_dollar,
            "out_revenue": revenue_som,
            "out_revenue_in_dollar": revenue_dollar,
            "out_cogs": cogs_som,
            "out_cogs_in_dollar": cogs_dollar,
        }
