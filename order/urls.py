from django.urls import path, include
from rest_framework.routers import DefaultRouter
from order.views.stats_views import OrderStatsView, CuttingBandingIncomeStatsView
from order.views.views import BasketViewSet, CuttingViewSet, BandingViewSet, ThicknessViewSet, OrderViewSet

router = DefaultRouter()
router.register('basket', BasketViewSet, basename='basket')
router.register('cutting', CuttingViewSet, basename='cutting')
router.register('banding', BandingViewSet, basename='banding')
router.register('thickness', ThicknessViewSet, basename='thickness')
router.register('order', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path("stats/order/", OrderStatsView.as_view()),
    path("income/cutting-banding/", CuttingBandingIncomeStatsView.as_view(), name="cutting-banding-income"),
]
