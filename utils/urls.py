from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.views.dashboard import DashboardStatsView, DashboardRangeStatsAPIView, DashboardDailyStatsAPIView, \
    CashboxTotalStatsAPIView
from utils.views.expenses import ExpenseViewSet, ExpenseHistoryViewSet
from utils.views.utils import CurrencyViewSet, LowStockNotificationView

router = DefaultRouter()
router.register('currency', CurrencyViewSet, basename='currency')
router.register("expenses", ExpenseViewSet)
router.register("history-expenses", ExpenseHistoryViewSet, basename='expenses-history')

urlpatterns = [
    path('', include(router.urls)),
    path("notifications/low-stock/", LowStockNotificationView.as_view(), name="stock-notification"),
    path("dashboard/stats/", DashboardStatsView.as_view()),
    path("range/stats/", DashboardRangeStatsAPIView.as_view()),
    path("daily/stats/", DashboardDailyStatsAPIView.as_view()),
    path("cashbox/stats/", CashboxTotalStatsAPIView.as_view())
]
