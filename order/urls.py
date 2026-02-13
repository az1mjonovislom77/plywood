from django.urls import path, include
from rest_framework.routers import DefaultRouter

from order.views import BasketViewSet

router = DefaultRouter()
router.register('basket', BasketViewSet, basename='basket')

urlpatterns = [
    path('', include(router.urls))
]
