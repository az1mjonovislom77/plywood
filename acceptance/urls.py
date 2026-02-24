from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AcceptanceViewSet, AcceptanceHistoryViewSet, UpdateCurrencyRateView

router = DefaultRouter()

router.register("acceptances", AcceptanceViewSet, basename="acceptance")
router.register("history", AcceptanceHistoryViewSet, basename="acceptance-history")

urlpatterns = [
    path('', include(router.urls)),
    path('currency/', UpdateCurrencyRateView.as_view()),
]
