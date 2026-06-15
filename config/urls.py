from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from utils.api.views.health import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('user/', include('user.api.urls')),
    path('product/', include('product.api.urls')),
    path('category/', include('category.api.urls')),
    path('customer/', include('customer.api.urls')),
    path('utils/', include('utils.api.urls')),
    path('acceptance/', include('acceptance.api.urls')),
    path('order/', include('order.api.urls')),
    path('supplier/', include('supplier.api.urls')),
    path('employee/', include('employee.api.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
