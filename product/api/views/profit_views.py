from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField, Case, When
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from product.services.export_json import MaterialReportJsonService
from acceptance.models import CurrencyRate
from order.models import OrderItem
from category.models import Category
from utils.models import Services, ServicesName


@extend_schema(tags=["Products"], parameters=[
    OpenApiParameter(name="from", required=False, type=OpenApiTypes.STR),
    OpenApiParameter(name="to", required=False, type=OpenApiTypes.STR),
])
class ProfitByCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")

        start_date, end_date, start_dt, end_dt = MaterialReportJsonService._parse_bounds(date_from, date_to)
        out_revenue_qs = (
            OrderItem.objects.filter(
                MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt)
            )
            .values("product_id")
            .annotate(
                out_revenue_in_dollar=Coalesce(
                    Sum(
                        F("quantity") * Case(
                            When(new_price_in_dollar__isnull=False, then=F("new_price_in_dollar")),
                            default=F("price_in_dollar"),
                            output_field=DecimalField(max_digits=18, decimal_places=4),
                        )
                    ), Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=4)
                )
            )
        )
        out_revenue_in_dollar_map = {r["product_id"]: Decimal(str(r.get("out_revenue_in_dollar") or 0)) for r in
                                     out_revenue_qs}

        open_cogs_map, period_cogs_map, open_cogs_map_in_dollar, period_cogs_map_in_dollar = MaterialReportJsonService._calc_fifo(
            start_dt, end_dt, end_date)
        
        # Bugungi kursni olish
        rate_obj = CurrencyRate.objects.filter(date=timezone.localdate()).first()
        rate_value = Decimal(rate_obj.rate) if rate_obj else Decimal("0")

        categories = list(Category.objects.all().order_by("name"))

        result_categories = []
        total_profit_dollar = Decimal("0")
        total_profit_som = Decimal("0")

        for category in categories:
            if category.name.strip().upper() == "KROMKA":
                continue

            products = category.products.all()
            cat_profit_som = Decimal("0")
            cat_profit_dollar = Decimal("0")

            for product in products:
                pid = product.id
                out_revenue_in_dollar = out_revenue_in_dollar_map.get(pid, Decimal("0"))
                out_cogs_in_dollar = period_cogs_map_in_dollar.get(pid, Decimal("0"))

                profit_dollar = out_revenue_in_dollar - out_cogs_in_dollar
                if rate_value and rate_value != Decimal("0"):
                    profit_som = (profit_dollar * rate_value).quantize(Decimal("0.01"))
                else:
                    out_revenue_som = Decimal("0")
                    out_cogs_som = period_cogs_map.get(pid, Decimal("0"))
                    profit_som = out_revenue_som - out_cogs_som
                cat_profit_dollar += profit_dollar
                cat_profit_som += profit_som
            total_profit_dollar += cat_profit_dollar
            total_profit_som += cat_profit_som

            result_categories.append({
                "id": category.id,
                "name": category.name,
                "profit_som": float(cat_profit_som),
                "profit_dollar": float(cat_profit_dollar),
            })

        return Response({
            "from": str(start_date),
            "to": str(end_date),
            "categories": result_categories,
            "total_profit_som": float(total_profit_som),
            "total_profit_dollar": float(total_profit_dollar),
        })


@extend_schema(tags=["Cutting"], parameters=[
    OpenApiParameter(name="from", required=False, type=OpenApiTypes.STR),
    OpenApiParameter(name="to", required=False, type=OpenApiTypes.STR),
])
class CuttingProfitView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        start_date, end_date, start_dt, end_dt = MaterialReportJsonService._parse_bounds(date_from, date_to)
        from utils.service.comprehensive_stats import DashboardStatsService as ComprehensiveDashboard

        stats = ComprehensiveDashboard.get_stats(date_from, date_to)
        cutting_som = Decimal(str(stats.get("cutting_sales", 0)))
        
        # Bugungi kursni olish
        rate_obj = CurrencyRate.objects.filter(date=timezone.localdate()).first()
        rate_value = Decimal(rate_obj.rate) if rate_obj else Decimal("0")
        
        cutting_dollar = Decimal("0")
        if rate_value and rate_value != Decimal("0"):
            cutting_dollar = (cutting_som / rate_value).quantize(Decimal("0.01"))
        kromka = Category.objects.filter(name__iexact="KROMKA").first()

        banding_qs = OrderItem.objects.filter(
            MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt),
            product__category=kromka, banding__isnull=False,
        ).aggregate(
            banding_som=Coalesce(
                Sum(F("banding__length") * F("banding__thickness") - Coalesce(F("banding__discount"),
                                                                              Value(Decimal("0")))),
                Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=2)
            )
        )

        banding_som = Decimal(str(banding_qs.get("banding_som") or 0))
        banding_dollar = Decimal("0")
        if rate_value and rate_value != Decimal("0"):
            banding_dollar = (banding_som / rate_value).quantize(Decimal("0.01"))

        services_names = ServicesName.objects.all()
        services_stats = []
        total_services_profit_som = Decimal("0")
        total_services_profit_dollar = Decimal("0")

        for service_name in services_names:
            service_total_som = Services.objects.filter(
                services_name=service_name, created_at__gte=start_dt, created_at__lt=end_dt
            ).aggregate(
                total=Coalesce(Sum('total_price'), Value(Decimal('0')), output_field=DecimalField()))['total']

            service_total_dollar = Decimal("0")
            if rate_value and rate_value != Decimal("0"):
                service_total_dollar = (service_total_som / rate_value).quantize(Decimal("0.01"))

            services_stats.append({
                "service_name": service_name.name,
                "profit_som": float(service_total_som),
                "profit_dollar": float(service_total_dollar),
            })
            total_services_profit_som += service_total_som
            total_services_profit_dollar += service_total_dollar

        return Response({
            "from": date_from or str(timezone.localdate()),
            "to": date_to or str(timezone.localdate()),
            "cutting_profit_som": float(cutting_som),
            "cutting_profit_dollar": float(cutting_dollar),
            "kromka_xizmat_profit_som": float(banding_som),
            "kromka_xizmat_profit_dollar": float(banding_dollar),
            "services_stats": services_stats,
            "total_services_profit_som": float(total_services_profit_som),
            "total_services_profit_dollar": float(total_services_profit_dollar),
        })


@extend_schema(tags=["Products"], parameters=[
    OpenApiParameter(name="from", required=False, type=OpenApiTypes.STR),
    OpenApiParameter(name="to", required=False, type=OpenApiTypes.STR),
])
class KromkaProfitView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        start_date, end_date, start_dt, end_dt = MaterialReportJsonService._parse_bounds(date_from, date_to)
        kromka = Category.objects.filter(name__iexact="KROMKA").first()
        if not kromka:
            return Response({"error": "KROMKA category not found"}, status=404)
        out_revenue_qs = (
            OrderItem.objects.filter(
                MaterialReportJsonService._accepted_order_range_filter(start_dt, end_dt),
                product__category=kromka,
            )
            .values("product_id")
            .annotate(
                out_revenue_in_dollar=Coalesce(
                    Sum(
                        F("quantity") * Case(
                            When(new_price_in_dollar__isnull=False, then=F("new_price_in_dollar")),
                            default=F("price_in_dollar"),
                            output_field=DecimalField(max_digits=18, decimal_places=4),
                        )
                    ), Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=4)
                )
            )
        )
        out_revenue_in_dollar_map = {r["product_id"]: Decimal(str(r.get("out_revenue_in_dollar") or 0)) for r in
                                     out_revenue_qs}

        open_cogs_map, period_cogs_map, open_cogs_map_in_dollar, period_cogs_map_in_dollar = MaterialReportJsonService._calc_fifo(
            start_dt, end_dt, end_date)
        
        # Bugungi kursni olish
        rate_obj = CurrencyRate.objects.filter(date=timezone.localdate()).first()
        rate_value = Decimal(rate_obj.rate) if rate_obj else Decimal("0")
        
        cat_products = kromka.products.all()
        product_profit_dollar = Decimal("0")
        product_profit_som = Decimal("0")

        for product in cat_products:
            pid = product.id
            out_revenue_in_dollar = out_revenue_in_dollar_map.get(pid, Decimal("0"))
            out_cogs_in_dollar = period_cogs_map_in_dollar.get(pid, Decimal("0"))
            profit_dollar = out_revenue_in_dollar - out_cogs_in_dollar
            if rate_value and rate_value != Decimal("0"):
                profit_som = (profit_dollar * rate_value).quantize(Decimal("0.01"))
            else:
                profit_som = period_cogs_map.get(pid, Decimal("0")) * Decimal("-1")

            product_profit_dollar += profit_dollar
            product_profit_som += profit_som

        return Response({
            "from": str(start_date),
            "to": str(end_date),
            "kromka_product_profit_som": float(product_profit_som),
            "kromka_product_profit_dollar": float(product_profit_dollar),
        })