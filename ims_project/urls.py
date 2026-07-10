from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# bellow is for locally media serve when debug is false
from django.urls import re_path
from django.views.static import serve

# ==========================================================
# PROJECT URLS
# ==========================================================
urlpatterns = [
    # Step 1: Django admin site
    path('admin/', admin.site.urls),

    # Step 2: Authentication app (signup, login, logout, password reset)
    path('', include('authenticate_app.urls')),

    # Step 3: Product app (categories, brands, product groups, products)
    path('', include('product_app.urls')),

    # Step 4: Dashboard app (main dashboard views)
    path('', include('dashboard_app.urls')),

    # Step 5: Stock app (opening stock, purchases, sales, returns, rejects)
    path('', include('stock_app.urls')),

    # Step 6: Person info app (suppliers, customers)
    path('', include("personinfo_app.urls")),

    # Step 7: Report app (report generation and downloads)
    path("reports/", include("report_app.urls")),

    # Stock reservation API endpoints (live stock system)
    path('stock/lookup/', __import__('stock_app.views', fromlist=['stock_lookup_by_barcode']).stock_lookup_by_barcode, name='stock_lookup_api'),
    path('stock/reserve/', __import__('stock_app.views', fromlist=['stock_reserve']).stock_reserve, name='stock_reserve_api'),
    path('stock/available/', __import__('stock_app.views', fromlist=['stock_available_bulk']).stock_available_bulk, name='stock_available_api'),
    path('stock/debug/', __import__('stock_app.views', fromlist=['stock_debug']).stock_debug, name='stock_debug_api'),

    #For language change.
    path('i18n/', include('django.conf.urls.i18n')),
]

# ==========================================================
# STATIC & MEDIA FILES (Local testing)
# ==========================================================

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# ==========================================================
# CUSTOM ERROR HANDLERS
# ==========================================================
handler404 = "ims_project.error_handlers.handler404"
handler500 = "ims_project.error_handlers.handler500"
handler403 = "ims_project.error_handlers.handler403"