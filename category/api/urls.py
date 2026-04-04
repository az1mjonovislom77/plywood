from django.urls import path, include
from rest_framework.routers import DefaultRouter
from category.api.views import CategoryViewSet

router = DefaultRouter()
router.register('category', CategoryViewSet, basename='category')

urlpatterns = [
    path('', include(router.urls)),
]
