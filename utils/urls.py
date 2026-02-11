from django.urls import path, include
from rest_framework.routers import DefaultRouter
from utils.views import CurrencyViewSet

router = DefaultRouter()
router.register('currency', CurrencyViewSet, basename='currency')

urlpatterns = [
    path('', include(router.urls)),
]
