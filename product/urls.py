from django.urls import path, include
from rest_framework.routers import DefaultRouter

from product.views import ProductViewSet, QualityViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('quality', QualityViewSet, basename='quality')

urlpatterns = [
    path('', include(router.urls)),

]
