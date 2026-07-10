from django.urls import path
from . import views

# ==========================================================
# STOCK APP URLS (Tenant-aware friendly)
# ==========================================================
urlpatterns = [
    # ======================================================
    # OPENING STOCK
    # ======================================================
    # Step 1: Create opening stock
    path('opening-stock/add/', views.add_opening_stock, name='add_opening_stock'),
    # Step 2: List opening stock entries (scoped in view by org/branch)
    path('opening-stock/', views.opening_stock_list, name='view_opening_stock'),
    # Step 3: Detail by primary key (safe for multi-tenant)
    path('opening-stock/<str:code>/', views.opening_stock_detail, name='opening_stock_detail'),

    # ======================================================
    # PURCHASE
    # ======================================================
    # Step 4: Create purchase
    path('purchase/add/', views.add_purchase, name='add_purchase'),
    # Step 5: List purchases (scoped in view by org/branch)
    path('purchase/', views.purchase_list, name='view_purchase'),
    # Step 6: Detail by purchase_code (ensure per-org uniqueness in model)
    path('purchase/<str:purchase_code>/', views.purchase_detail, name='purchase_detail'),

    # ======================================================
    # SALE
    # ======================================================
    # Step 7: Create sale
    path('sale/add/', views.add_sale, name='add_sale'),
    # Step 8: List sales (scoped in view by org/branch)
    path('sale/', views.sale_list, name='view_sale'),
    # Step 9: Detail by sale_code (ensure per-org uniqueness in model)
    path('sale/<str:sale_code>/', views.sale_detail, name='sale_detail'),

    # ======================================================
    # PURCHASE RETURN
    # ======================================================
    # Step 10: Create purchase return
    path('purchase-return/add/', views.add_purchase_return, name='add_purchase_return'),
    # Step 11: List purchase returns (scoped in view by org/branch)
    path('purchase-return/', views.purchase_return_list, name='view_purchase_return'),
    # Step 12: Detail by return_code (ensure per-org uniqueness in model)
    path('purchase-return/<str:return_code>/', views.purchase_return_detail, name='purchase_return_detail'),

    # ======================================================
    # SALE RETURN
    # ======================================================
    # Step 13: Create sale return
    path('sale-return/add/', views.add_sale_return, name='add_sale_return'),
    # Step 14: List sale returns (scoped in view by org/branch)
    path('sale-return/', views.sale_return_list, name='view_sale_return'),
    # Step 15: Detail by return_code (ensure per-org uniqueness in model)
    path('sale-return/<str:return_code>/', views.sale_return_detail, name='sale_return_detail'),

    # ======================================================
    # PRODUCT REJECT
    # ======================================================
    # Step 16: Create reject entry
    path('reject/add/', views.add_reject, name='add_reject'),
    # Step 17: List rejects (scoped in view by org/branch)
    path('reject/', views.reject_list, name='view_reject'),
    # Step 18: Detail by primary key (safe for multi-tenant)
    path('reject/<str:reject_code>/', views.reject_detail, name='reject_detail'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),


    # ======================================================
    # BARCODE LOOKUP
    # ======================================================
    path('lookup/', views.stock_lookup_by_barcode, name='stock_lookup_by_barcode'),

    # ======================================================
    # STOCK RESERVATION (live available-stock system)
    # ======================================================
    # POST/GET: reserve or check stock for a product in current session
    path('reserve/', views.stock_reserve, name='stock_reserve'),
    # GET: bulk available stock for multiple products (used for live polling)
    path('available/', views.stock_available_bulk, name='stock_available_bulk'),
    # Debug — remove after confirming reservations work
    path('debug/', views.stock_debug, name='stock_debug'),

]