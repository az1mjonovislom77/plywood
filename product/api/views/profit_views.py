from decimal import Decimal
from django.db.models import Value, Sum, DecimalField
from django.db.models.functions import Coalesce
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from category.models import Category
from customer.models import Customer
from employee.models import SalaryPayment
from product.services.ancillary_profit import AncillaryProfitService
from product.services.material_profit import KROMKA_CATEGORY_NAME, MaterialProfitService
from product.services.product_export import MaterialReportService
from product.services.total_profit import AllProfitService
from utils.models import Expenses
from utils.service.comprehensive_stats import DashboardStatsService


@extend_schema(tags=["Products"], parameters=[
    OpenApiParameter(name="from", required=False, type=OpenApiTypes.STR),
    OpenApiParameter(name="to", required=False, type=OpenApiTypes.STR),
])
class ProfitByCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("from")
        date_to = request.query_params.get("to")
        context = MaterialProfitService.build_profit_context(date_from, date_to)
        profits = MaterialProfitService.calc_profits_by_category(
            context, exclude_kromka=True
        )

        return Response({
            "from": str(context["start_date"]),
            "to": str(context["end_date"]),
            "categories": profits["categories"],
            "total_profit_som": float(profits["total_profit_som"]),
            "total_profit_dollar": float(profits["total_profit_dollar"]),
            "products_count": profits["products_count"],
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
        context = MaterialProfitService.build_profit_context(date_from, date_to)
        ancillary = AncillaryProfitService.calc_all_ancillary(
            date_from,
            date_to,
            context["start_dt"],
            context["end_dt"],
            context["end_date"],
        )

        return Response({
            "from": date_from or str(timezone.localdate()),
            "to": date_to or str(timezone.localdate()),
            "cutting_profit_som": float(ancillary["cutting_som"]),
            "cutting_profit_dollar": float(ancillary["cutting_dollar"]),
            "kromka_xizmat_profit_som": float(ancillary["banding_som"]),
            "kromka_xizmat_profit_dollar": float(ancillary["banding_dollar"]),
            "services_stats": ancillary["services_stats"],
            "total_services_profit_som": float(ancillary["services_som"]),
            "total_services_profit_dollar": float(ancillary["services_dollar"]),
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
        context = MaterialProfitService.build_profit_context(date_from, date_to)
        kromka = Category.objects.filter(name__iexact=KROMKA_CATEGORY_NAME).first()
        if not kromka:
            return Response({"error": "KROMKA category not found"}, status=404)

        product_profit_som, product_profit_dollar, products_count = (
            MaterialProfitService.calc_kromka_product_profit(context))
        all_profit = AllProfitService.calculate(
            date_from=date_from,
            date_to=date_to,
            start_dt=context["start_dt"],
            end_dt=context["end_dt"],
            end_date=context["end_date"],
            context=context,
        )

        money_field = DecimalField(max_digits=18, decimal_places=2)

        salary_total = (
                SalaryPayment.objects.filter(
                    paid_at__gte=context["start_dt"],
                    paid_at__lt=context["end_dt"]
                ).aggregate(
                    total=Coalesce(Sum("amount"), Value(Decimal("0")), output_field=money_field)
                )["total"] or Decimal("0"))

        expense_total = (
                Expenses.objects.filter(
                    created_at__gte=context["start_dt"],
                    created_at__lt=context["end_dt"],
                    expense_status__in=[
                        Expenses.ExpensesStatus.CREATED,
                        Expenses.ExpensesStatus.ACCEPT,
                    ]
                ).aggregate(
                    total=Coalesce(Sum("value"), Value(Decimal("0")), output_field=money_field)
                )["total"] or Decimal("0"))

        total_expenses = salary_total + expense_total
        itog_natsenka = Decimal(str(all_profit["all_profit_som"]))
        net_profit = itog_natsenka - total_expenses

        sklad = MaterialReportService.calc_inventory_total(context)

        qarzdorlik = (
            Customer.objects.aggregate(
                total=Coalesce(Sum("debt"), Value(Decimal("0")), output_field=money_field)
            )["total"] or Decimal("0")
        )

        kassa = Decimal(str(DashboardStatsService._cashbox_total()))

        rate_value = context["rate_value"]
        itog_rasxod_dollar = (total_expenses / rate_value) if rate_value else Decimal("0")
        net_profit_dollar = (net_profit / rate_value) if rate_value else Decimal("0")
        sklad_dollar = sklad
        sklad_som = (sklad_dollar * rate_value) if rate_value else Decimal("0")
        qarzdorlik_dollar = (qarzdorlik / rate_value) if rate_value else Decimal("0")
        kassa_dollar = (kassa / rate_value) if rate_value else Decimal("0")
        jami_som = sklad_som + qarzdorlik + kassa
        jami_dollar = sklad_dollar + qarzdorlik_dollar + kassa_dollar

        return Response({
            "from": str(context["start_date"]),
            "to": str(context["end_date"]),
            "kromka_product_profit_som": float(product_profit_som),
            "kromka_product_profit_dollar": float(product_profit_dollar),
            "kromka_products_count": products_count,
            "itog_rasxod": float(total_expenses),
            "itog_rasxod_in_dollar": float(itog_rasxod_dollar),
            "net_profit": float(net_profit),
            "net_profit_in_dollar": float(net_profit_dollar),
            "sklad": float(sklad_som),
            "sklad_in_dollar": float(sklad_dollar),
            "qarzdorlik": float(qarzdorlik),
            "qarzdorlik_in_dollar": float(qarzdorlik_dollar),
            "jami": float(jami_som),
            "jami_in_dollar": float(jami_dollar),
            **all_profit,
        })
