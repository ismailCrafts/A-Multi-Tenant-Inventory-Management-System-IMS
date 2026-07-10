from django.urls import path
from . import views

# ==========================================================
# PRODUCT APP URLS
# NOTE: Specific paths (add/, update/, delete/) MUST come
# before dynamic <str:name>/ to avoid route shadowing.
# ==========================================================
urlpatterns = [
    # ==========================================================
    # CATEGORY URLS
    # ==========================================================
    path('categories/',                       views.view_category,      name='view_category'),
    path('categories/add/',                   views.add_category,        name='add_category'),
    path('categories/update/<str:name>/',     views.update_category,    name='update_category'),
    path('categories/delete/<str:name>/',     views.delete_category,    name='delete_category'),
    path('categories/<str:name>/',            views.category_detail,    name='category_detail'),

    # ==========================================================
    # BRAND URLS
    # ==========================================================
    path('brands/',                           views.view_brand,          name='view_brand'),
    path('brands/add/',                       views.add_brand,           name='add_brand'),
    path('brands/update/<str:name>/',         views.update_brand,       name='update_brand'),
    path('brands/delete/<str:name>/',         views.delete_brand,       name='delete_brand'),
    path('brands/<str:name>/',                views.brand_detail,        name='brand_detail'),

    # ==========================================================
    # PRODUCT GROUP URLS
    # ==========================================================
    path('productgroups/',                    views.view_productgroup,      name='view_productgroup'),
    path('productgroups/add/',                views.add_productgroup,        name='add_productgroup'),
    path('productgroups/update/<str:name>/',  views.update_productgroup,    name='update_productgroup'),
    path('productgroups/delete/<str:name>/',  views.delete_productgroup,    name='delete_productgroup'),
    path('productgroups/<str:name>/',         views.productgroups_detail,    name='productgroups_detail'),

    # ==========================================================
    # PRODUCT URLS
    # ==========================================================
    path('products/',                         views.view_product,        name='view_product'),
    path('products/add/',                     views.add_product,         name='add_product'),
    path('products/update/<str:name>/',       views.update_product,     name='update_product'),
    path('products/delete/<str:name>/',       views.delete_product,     name='delete_product'),
    path('products/<str:name>/',              views.product_detail,      name='product_detail'),
]