from django.urls import path, include
from rest_framework.routers import DefaultRouter
from employee.api.views import EmployeeViewSet

router = DefaultRouter()
router.register('employee', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls))
]
