from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.views import CurrencyViewSet, LowStockNotificationView, DashboardStatsView, DashboardRangeStatsAPIView

router = DefaultRouter()
router.register('currency', CurrencyViewSet, basename='currency')

urlpatterns = [
    path('', include(router.urls)),
    path("notifications/low-stock/", LowStockNotificationView.as_view(), name="stock-notification"),
    path("dashboard/stats/", DashboardStatsView.as_view()),
    path("range/stats/", DashboardRangeStatsAPIView.as_view()),

]
