from django.urls import path, include
from rest_framework.routers import DefaultRouter

from order.views import BasketViewSet, CuttingViewSet, BandingViewSet, ThicknessViewSet, OrderViewSet

router = DefaultRouter()
router.register('basket', BasketViewSet, basename='basket')
router.register('cutting', CuttingViewSet, basename='cutting')
router.register('banding', BandingViewSet, basename='banding')
router.register('thickness', ThicknessViewSet, basename='thickness')
router.register('order', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls))
]
