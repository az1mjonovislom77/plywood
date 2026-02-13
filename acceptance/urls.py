from rest_framework.routers import DefaultRouter
from .views import AcceptanceViewSet, AcceptanceHistoryViewSet

router = DefaultRouter()

router.register("acceptances", AcceptanceViewSet, basename="acceptance")
router.register("acceptance-histories", AcceptanceHistoryViewSet, basename="acceptance-history")

urlpatterns = router.urls
