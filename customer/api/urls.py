from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customer.api.views.stats_views import CustomerStatsView, DashboardDebtStatsView
from customer.api.views.customer import CustomerViewSet, CustomerStatementExcelViewSet, CustomerDebtExcelAPIView, \
    CustomerDebtReportJsonAPIView
from customer.api.views.debt import CoverDebtAPIView, CustomerHistoryAPIView, CustomerStatementExcelAPIView

router = DefaultRouter()
router.register('customer', CustomerViewSet, basename='customer')
router.register('export', CustomerStatementExcelViewSet, basename='export')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/customers/', CustomerStatsView.as_view(), name='customers_stats'),
    path('stats/debt/', DashboardDebtStatsView.as_view(), name='debt_stats'),
    path("cover-debt/<int:pk>/", CoverDebtAPIView.as_view()),
    path("payment-history/<int:pk>/", CustomerHistoryAPIView.as_view()),
    path("statement-excel/<int:pk>/", CustomerStatementExcelAPIView.as_view()),
    path('debt/excel/', CustomerDebtExcelAPIView.as_view()),
    path("debt/json/", CustomerDebtReportJsonAPIView.as_view(), name="customer-debt-report"),
]
