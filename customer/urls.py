from django.urls import path, include
from customer.views.stats_views import CustomerStatsView, DashboardDebtStatsView
from customer.views.views import CustomerViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('customer', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
    path('stats/customers/', CustomerStatsView.as_view(), name='customers_stats'),
    path('stats/debt/', DashboardDebtStatsView.as_view(), name='debt_stats')
]
