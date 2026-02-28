from django.urls import path, include
from rest_framework.routers import DefaultRouter
from supplier.views import SupplierPaymentView, SupplierTransactionView, SupplierViewSet, SupplierDebtStatsView

router = DefaultRouter()
router.register('supplier', SupplierViewSet, basename='supplier')

urlpatterns = [
    path('', include(router.urls)),
    path("payment/", SupplierPaymentView.as_view(), name="supplier-payment"),
    path("<int:supplier_id>/transactions/", SupplierTransactionView.as_view(), name="supplier-transactions"),
    path("stats/", SupplierDebtStatsView.as_view(), name="supplier-stats"),
]
