from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.api.views.dashboard import ComprehensiveDashboardStatsAPIView
from utils.api.views.expenses import ExpenseViewSet, ExpenseHistoryViewSet, CashFlowReportExcelViewSet, \
    FinanceReportJsonViewSet
from utils.api.views.utils import CurrencyViewSet, LowStockNotificationView, ServicesViewSet

router = DefaultRouter()
router.register('currency', CurrencyViewSet, basename='currency')
router.register("expenses", ExpenseViewSet)
router.register("history-expenses", ExpenseHistoryViewSet, basename='expenses-history')
router.register("services", ServicesViewSet, basename='services')

urlpatterns = [
    path('', include(router.urls)),
    path("notifications/low-stock/", LowStockNotificationView.as_view(), name="stock-notification"),
    path("all-stats/", ComprehensiveDashboardStatsAPIView.as_view()),
    path("export/", CashFlowReportExcelViewSet.as_view({"get": "list"}), name="cashflow-report"),
    path("finance-report/", FinanceReportJsonViewSet.as_view({"get": "list"})),
]
