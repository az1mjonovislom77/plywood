from django.urls import path, include
from rest_framework.routers import DefaultRouter

from order.views import BasketViewSet, CuttingViewSet

router = DefaultRouter()
router.register('basket', BasketViewSet, basename='basket')
router.register('cutting', CuttingViewSet, basename='cutting')

urlpatterns = [
    path('', include(router.urls))
]
