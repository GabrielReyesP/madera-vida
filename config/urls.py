"""
config/urls.py
URLs principales de Madera & Vida.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin de Django (solo superusuarios)
    path('admin/', admin.site.urls),

    # Apps del proyecto
    path('', include('apps.catalog.urls')),          # Landing + catálogo público
    path('accounts/', include('apps.accounts.urls')), # Login, registro, perfiles
    path('store/', include('apps.store.urls')),       # Carrito, checkout, pedidos
    path('hr/', include('apps.hr.urls')),             # Recursos Humanos
    path('dashboard/', include('apps.dashboard.urls')), # Panel administrativo
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personalizar títulos del admin de Django
admin.site.site_header = 'Madera & Vida - Administración'
admin.site.site_title = 'Madera & Vida'
admin.site.index_title = 'Panel de Control'