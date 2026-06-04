from django.urls import path, include
from rest_framework.routers import DefaultRouter
from product.api.views.product_views import ProductViewSet, MaterialReportExcelViewSet, MaterialReportJsonViewSet, \
    DeletedProductsViewSet
from product.api.views.quality_views import QualityViewSet
from product.api.views.profit_views import ProfitByCategoryView, KromkaProfitView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('quality', QualityViewSet, basename='quality')

urlpatterns = [
    path('', include(router.urls)),
    path("export/", MaterialReportExcelViewSet.as_view({"get": "list"}), name="material-report"),
    path("product-report/", MaterialReportJsonViewSet.as_view({"get": "list"})),
    path("profit-category/", ProfitByCategoryView.as_view(), name="profit-by-category"),
    path("kromka-profit/", KromkaProfitView.as_view(), name="kromka-profit"),
    path("deleted-products/", DeletedProductsViewSet.as_view({"get": "list"})),
]
