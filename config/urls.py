"""URL root configuration — mounts semua app ke path masing-masing."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('cart/', include('apps.cart.urls')),
    path('order/', include('apps.order.urls')),
    path('recommendations/', include('apps.recommendations.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # produk last — root path '/' harus match listing
    path('', include('apps.catalog.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
