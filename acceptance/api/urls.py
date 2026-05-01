from django.urls import path, include
from rest_framework.routers import DefaultRouter
from acceptance.api.views.acceptance_history_views import AcceptanceHistoryViewSet
from acceptance.api.views.acceptance_views import AcceptanceViewSet, AcceptanceAnalyticsViewSet, \
    AcceptanceExportViewSet, AcceptanceSuppliersViewSet
from acceptance.api.views.currency_views import UpdateCurrencyRateView

router = DefaultRouter()

router.register("acceptances", AcceptanceViewSet, basename="acceptance")
router.register("history", AcceptanceHistoryViewSet, basename="acceptance-history")
router.register("analytics", AcceptanceAnalyticsViewSet, basename="analytics")
router.register("suppliers", AcceptanceSuppliersViewSet, basename="suppliers")
router.register("acceptance-export", AcceptanceExportViewSet, basename="acceptance-export")

urlpatterns = [
    path('', include(router.urls)),
    path('currency/', UpdateCurrencyRateView.as_view()),
]
