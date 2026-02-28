from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
import debug_toolbar

from product.views import show_ip

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('product/', include('product.urls')),
    path('category/', include('category.urls')),
    path('customer/', include('customer.urls')),
    path('utils/', include('utils.urls')),
    path('acceptance/', include('acceptance.urls')),
    path('order/', include('order.urls')),
    path('supplier/', include('supplier.urls')),
    path("ip/", show_ip),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("__debug__/", include(debug_toolbar.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
