# product_app/admin.py
from django.contrib import admin
from .models import Category, Brand, ProductGroup, Product


# ==========================================================
# CATEGORY ADMIN
# ==========================================================
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category.
    Steps:
    1. Show name, organization, branch, created_at in list view.
    2. Enable search by name.
    3. Add filters for organization, branch, created_at.
    4. Make created_at read-only.
    """
    list_display = ('name', 'organization', 'branch', 'created_at')
    search_fields = ('name',)
    list_filter = ('organization', 'branch', 'created_at')
    readonly_fields = ('created_at',)


# ==========================================================
# BRAND ADMIN
# ==========================================================
class BrandAdmin(admin.ModelAdmin):
    """
    Admin configuration for Brand.
    Steps:
    1. Show name, brand_code, organization, branch, created_at.
    2. Enable search by name and code.
    3. Add filters for organization, branch, created_at.
    4. Make created_at read-only.
    """
    list_display = ('name', 'code', 'organization', 'branch', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('organization', 'branch', 'created_at')
    readonly_fields = ('created_at',)


# ==========================================================
# PRODUCT GROUP ADMIN
# ==========================================================
class ProductGroupAdmin(admin.ModelAdmin):
    """
    Admin configuration for ProductGroup.
    Steps:
    1. Show name, code, category, brand, organization, branch, created_at.
    2. Enable search by name and code.
    3. Add filters for category, brand, organization, branch, created_at.
    4. Make created_at read-only.
    """
    list_display = ('name', 'code', 'category', 'brand', 'organization', 'branch', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('category', 'brand', 'organization', 'branch', 'created_at')
    readonly_fields = ('created_at',)


# ==========================================================
# PRODUCT ADMIN
# ==========================================================
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product.
    Steps:
    1. Show name, code, barcode_number, category, brand, product_group, organization, branch, created_at.
    2. Enable search by name, code, barcode_number.
    3. Add filters for category, brand, product_group, organization, branch, created_at.
    4. Make created_at read-only.
    """
    list_display = (
        'name', 'code', 'barcode_number',
        'category', 'brand', 'product_group',
        'organization', 'branch', 'created_at'
    )
    search_fields = ('name', 'code', 'barcode_number')
    list_filter = ('category', 'brand', 'product_group', 'organization', 'branch', 'created_at')
    readonly_fields = ('created_at',)


# ==========================================================
# REGISTER MODELS
# ==========================================================
admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(ProductGroup, ProductGroupAdmin)
admin.site.register(Product, ProductAdmin)
