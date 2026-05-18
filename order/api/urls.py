from django.urls import path, include
from rest_framework.routers import DefaultRouter
from order.api.views.stats import CuttingBandingIncomeStatsView, Last7DaysIncomeView
from order.api.views.banding import BandingViewSet
from order.api.views.basket import BasketViewSet
from order.api.views.cutting import CuttingViewSet
from order.api.views.history import OrderHistoryViewSet
from order.api.views.order import OrderViewSet, OrderExcelViewSet
from order.api.views.thickness import ThicknessViewSet

router = DefaultRouter()
router.register('basket', BasketViewSet, basename='basket')
router.register('cutting', CuttingViewSet, basename='cutting')
router.register('banding', BandingViewSet, basename='banding')
router.register('thickness', ThicknessViewSet, basename='thickness')
router.register('order', OrderViewSet, basename='order')
router.register("history", OrderHistoryViewSet, basename="order-history")
router.register("order-excel", OrderExcelViewSet, basename="order-excel")

urlpatterns = [
    path('', include(router.urls)),
    path("income/cutting-banding/", CuttingBandingIncomeStatsView.as_view(), name="cutting-banding-income"),
    path("last7days/", Last7DaysIncomeView.as_view()),
]
