from django.urls import path, include
from rest_framework.routers import DefaultRouter
from supplier.api.views.payment_views import SupplierPaymentView
from supplier.api.views.stats_views import SupplierDebtStatsView
from supplier.api.views.supplier_views import SupplierViewSet
from supplier.api.views.transaction_views import SupplierTransactionView

router = DefaultRouter()
router.register('supplier', SupplierViewSet, basename='supplier')

urlpatterns = [
    path('', include(router.urls)),
    path("payment/", SupplierPaymentView.as_view(), name="supplier-payment"),
    path("<int:supplier_id>/transactions/", SupplierTransactionView.as_view(), name="supplier-transactions"),
    path("stats/", SupplierDebtStatsView.as_view(), name="supplier-stats"),
]
