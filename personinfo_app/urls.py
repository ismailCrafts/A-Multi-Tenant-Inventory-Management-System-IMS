from django.urls import path
from . import views
from authenticate_app.views import change_password  

"""
URL configuration for profile, supplier, and customer routes.

Purpose and structure:
- Grouped by feature area (profile, supplier, customer) with clear step comments.
- Each path maps a URL pattern to a view and a named route for reverse lookups.
- Comments indicate the intended step or behavior for each route to aid maintainability.

Notes:
- Do not change the URL patterns or view imports; this file documents the routing intent only.
- The `change_password` view is imported directly from authenticate_app.views and reused here.
"""

urlpatterns = [

    # ---------------- PROFILE ROUTES ----------------
    path("", views.profile_view, name="profile"),
    # Profile main view: shows user profile page
    path("profile/", views.profile_view, name="profile"),

    # Profile update: form to update basic profile fields
    path("profile/update/", views.update_profile_view, name="update_profile"),

    # Change password: uses shared change_password view from authenticate_app
    path("profile/change-password/", change_password, name="password_change"),

    # Update profile image: endpoint to upload/replace profile picture
    path("profile/update-image/", views.update_profile_image, name="update_profile_image"),

    # Remove profile image: endpoint to delete current profile picture
    path("profile/remove-image/", views.remove_profile_image, name="remove_profile_image"),
    

    # ---------------- SUPPLIER ROUTES ----------------
    # Step 1: List all suppliers for the tenant/user
    path("supplier/list/", views.supplier_list, name="supplier_list"),

    # Step 2: Create a new supplier (form + POST handler)
    path("supplier/create/", views.supplier_create, name="supplier_create"),

    # Step 3: View supplier details by primary key (detail view)
    path("supplier/<int:pk>/", views.supplier_detail, name="supplier_detail"),

    # Step 4: Update supplier details by primary key (edit form + POST)
    path("supplier/<int:pk>/update/", views.supplier_update, name="supplier_update"),

    # Step 5: Lookup supplier by code or mobile (search/lookup endpoint)
    path("supplier/lookup/", views.supplier_lookup, name="supplier_lookup"),


    # ---------------- CUSTOMER ROUTES ----------------
    # Step 6: List all customers for the tenant/user
    path("customer/list/", views.customer_list, name="customer_list"),

    # Step 7: Create a new customer (form + POST handler)
    path("customer/create/", views.customer_create, name="customer_create"),

    # Step 8: View customer details by primary key (detail view)
    path("customer/<int:pk>/", views.customer_detail, name="customer_detail"),

    # Step 9: Update customer details by primary key (edit form + POST)
    path("customer/<int:pk>/update/", views.customer_update, name="customer_update"),

    # Step 10: Lookup customer by code or mobile (search/lookup endpoint)
    path("customer/lookup/", views.customer_lookup, name="customer_lookup"),
]
