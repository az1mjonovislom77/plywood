from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customer.api.views.stats_views import CustomerStatsView, DashboardDebtStatsView
from customer.api.views.customer_views import CustomerViewSet, CoverDebtAPIView, CustomerHistoryAPIView

router = DefaultRouter()
router.register('customer', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/customers/', CustomerStatsView.as_view(), name='customers_stats'),
    path('stats/debt/', DashboardDebtStatsView.as_view(), name='debt_stats'),
    path("cover-debt/<int:pk>/", CoverDebtAPIView.as_view()),
    path("payment-history/<int:pk>/", CustomerHistoryAPIView.as_view()),
]
