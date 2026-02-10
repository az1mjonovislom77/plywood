from django.urls import path, include
from rest_framework.routers import DefaultRouter
from customer.views import CustomerViewSet

router = DefaultRouter()
router.register('customer', CustomerViewSet, basename='customer')

urlpatterns = [
    path('', include(router.urls)),
]
