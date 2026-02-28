from django.urls import path, include
from rest_framework.routers import DefaultRouter

from product.views import ProductViewSet, QualityViewSet, show_ip

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('quality', QualityViewSet, basename='quality')

urlpatterns = [
    path('', include(router.urls)),
    path("ip/", show_ip),
]
