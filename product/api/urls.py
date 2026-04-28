from django.urls import path, include
from rest_framework.routers import DefaultRouter
from product.api.views.product_views import ProductViewSet, MaterialReportExcelViewSet
from product.api.views.quality_views import QualityViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('quality', QualityViewSet, basename='quality')

urlpatterns = [
    path('', include(router.urls)),
    path("export/", MaterialReportExcelViewSet.as_view({"get": "list"}), name="material-report")

]
