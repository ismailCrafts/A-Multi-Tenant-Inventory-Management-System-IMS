from django.contrib import admin
from .models import Supplier, Customer


# ==========================================================
# SUPPLIER ADMIN
# ==========================================================
class SupplierAdmin(admin.ModelAdmin):
    """
    Admin configuration for Supplier.
    Steps:
    1. Configure list display columns and default ordering.
    2. Add filters for quick narrowing (organization, branch).
    3. Enable search on key fields (code, name, mobile, email).
    4. Make audit fields read-only.
    5. Organize form layout with fieldsets.
    """

    # Step 1: Columns in changelist + ordering
    list_display = ('code', 'name', 'mobile', 'email', 'organization', 'branch', 'created_at')
    ordering = ('name',)

    # Step 2: Sidebar filters
    list_filter = ('organization', 'branch', 'created_at')

    # Step 3: Searchable fields
    search_fields = ('code', 'name', 'mobile', 'email')

    # Step 4: Read-only audit fields
    readonly_fields = ('created_at',)

    # Step 5: Form layout
    fieldsets = (
        ('Identity', {
            'fields': ('code', 'name', 'mobile', 'email'),
        }),
        ('Location', {
            'fields': ('organization', 'branch'),
        }),
        ('Additional', {
            'fields': ('address',),
        }),
        ('Audit', {
            'fields': ('created_at',),
        }),
    )

    list_per_page = 25


# ==========================================================
# CUSTOMER ADMIN
# ==========================================================
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Customer.
    Steps:
    1. Configure list display columns and default ordering.
    2. Add filters for quick narrowing (organization, branch).
    3. Enable search on key fields (code, name, mobile, email).
    4. Make audit fields read-only.
    5. Organize form layout with fieldsets.
    """

    # Step 1: Columns in changelist + ordering
    list_display = ('code', 'name', 'mobile', 'email', 'organization', 'branch', 'created_at')
    ordering = ('name',)

    # Step 2: Sidebar filters
    list_filter = ('organization', 'branch', 'created_at')

    # Step 3: Searchable fields
    search_fields = ('code', 'name', 'mobile', 'email')

    # Step 4: Read-only audit fields
    readonly_fields = ('created_at',)

    # Step 5: Form layout
    fieldsets = (
        ('Identity', {
            'fields': ('code', 'name', 'mobile', 'email'),
        }),
        ('Location', {
            'fields': ('organization', 'branch'),
        }),
        ('Additional', {
            'fields': ('address',),
        }),
        ('Audit', {
            'fields': ('created_at',),
        }),
    )

    list_per_page = 25


# ==========================================================
# REGISTER MODELS
# ==========================================================
# Step 0: Register Supplier with custom admin
admin.site.register(Supplier, SupplierAdmin)

# Step 0: Register Customer with custom admin
admin.site.register(Customer, CustomerAdmin)
