# stock_app/admin.py
from django.contrib import admin
from authenticate_app.models import Branch
from .models import (
    OpeningStock,
    Purchase, PurchaseItem,
    Sale, SaleItem,
    PurchaseReturn, PurchaseReturnItem,
    SaleReturn, SaleReturnItem,
    ProductReject, StockReservation,
)

# ==========================================================
# PLATFORM SUPERADMIN CHECK
# ==========================================================
def is_platform_superadmin(user) -> bool:
    """
    Platform-level superadmin checker.
    Step-by-step:
    1) Must be is_superuser=True
    2) Must have organization=None (global scope)
    """
    return user.is_superuser and getattr(user, "organization", None) is None


# ==========================================================
# BASE TENANT ADMIN MIXIN (FINAL)
# ==========================================================
class TenantScopedAdminMixin(admin.ModelAdmin):
    """
    Tenant-aware admin mixin.

    Guarantees (step-by-step):
    1) Queryset scoping:
       - Superadmin (organization=None) → sees ALL records.
       - Tenant users → filter by request.user.organization.
       - Optional: branch scoping can be applied if needed.

    2) Auto-assign organization on save for tenant users:
       - Organization is hidden/locked for tenant users.
       - Branch remains editable but dropdown is scoped to user's org.

    3) Scoped foreign key dropdowns:
       - Tenant users → branch choices limited to their org; org disabled/prefilled.
       - Superadmins → global dropdowns.
    """

    # 1) Queryset scoping
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        if is_platform_superadmin(user):
            return qs

        qs = qs.filter(organization=user.organization)

        # Optional policy:
        # If you want tenant users restricted to their own branch uncomment below:
        # if hasattr(qs.model, "branch") and user.branch:
        #     qs = qs.filter(branch=user.branch)

        return qs

    # 2) Auto-assign organization for tenant users (branch stays editable)
    def save_model(self, request, obj, form, change):
        user = request.user
        if not is_platform_superadmin(user):
            obj.organization = user.organization
        super().save_model(request, obj, form, change)

    # 3) Hide org for tenant users (prefer exclude; use readonly as a fallback)
    def get_exclude(self, request, obj=None):
        if not is_platform_superadmin(request.user):
            exclude = list(super().get_exclude(request, obj) or [])
            field_names = [f.name for f in self.model._meta.fields]
            if "organization" in field_names:
                exclude.append("organization")
            return tuple(set(exclude))
        return super().get_exclude(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if not is_platform_superadmin(request.user):
            ro = list(super().get_readonly_fields(request, obj))
            field_names = [f.name for f in self.model._meta.fields]
            if "organization" in field_names and "organization" not in ro:
                ro.append("organization")
            return tuple(ro)
        return super().get_readonly_fields(request, obj)

    # 4) Scope FK dropdowns (branch limited to user's org; org disabled and prefilled)
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        user = request.user

        if not is_platform_superadmin(user):
            if db_field.name == "organization":
                kwargs["initial"] = user.organization
                kwargs["disabled"] = True
            elif db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(organization=user.organization)
                if getattr(user, "branch", None):
                    kwargs["initial"] = user.branch

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # 5) Defensive list_filter cleanup (optional)
    def get_list_filter(self, request):
        base_filters = list(super().get_list_filter(request))
        field_names = [f.name for f in self.model._meta.fields]
        if "branch" not in field_names:
            base_filters = [f for f in base_filters if f != "branch"]
        return tuple(base_filters)


# ==========================================================
# INLINE ADMINS (SCOPED BRANCH, ORG REMOVED)
# ==========================================================
class BaseItemInline(admin.TabularInline):
    """
    Shared inline behavior for item inlines:
    - Org hidden; parent save stamps org via mixin.
    - Branch editable but scoped to user's org.
    """
    extra = 0
    show_change_link = True
    fields = ('category', 'product_group', 'brand', 'product', 'quantity', 'unit_price', 'subtotal', 'branch')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "branch" and not is_platform_superadmin(request.user):
            kwargs["queryset"] = Branch.objects.filter(organization=request.user.organization)
            if getattr(request.user, "branch", None):
                kwargs["initial"] = request.user.branch
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PurchaseItemInline(BaseItemInline):
    model = PurchaseItem


class SaleItemInline(BaseItemInline):
    model = SaleItem


class PurchaseReturnItemInline(BaseItemInline):
    model = PurchaseReturnItem


class SaleReturnItemInline(BaseItemInline):
    model = SaleReturnItem


# ==========================================================
# ADMIN CLASSES
# ==========================================================
class OpeningStockAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('date', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'stock', 'quantity', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'date', 'created_at')
    search_fields = ('product__name',)
    readonly_fields = ('created_at',)


class PurchaseAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('purchase_code', 'date', 'supplier_name', 'supplier_mobile', 'total_amount', 'paid_amount', 'due_amount', 'organization', 'branch', 'created_at')
    list_filter = ('organization', 'branch', 'date', 'created_at')
    search_fields = ('purchase_code', 'supplier_name', 'supplier_mobile')
    readonly_fields = ('created_at',)
    inlines = [PurchaseItemInline]


class PurchaseItemAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('purchase', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'created_at')
    search_fields = ('purchase__purchase_code', 'product__name')
    readonly_fields = ('created_at',)


class SaleAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('sale_code', 'date', 'customer_name', 'customer_mobile', 'total_amount', 'paid_amount', 'due_amount', 'organization', 'branch', 'created_at')
    list_filter = ('organization', 'branch', 'date', 'created_at')
    search_fields = ('sale_code', 'customer_name', 'customer_mobile')
    readonly_fields = ('created_at',)
    inlines = [SaleItemInline]


class SaleItemAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('sale', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'created_at')
    search_fields = ('sale__sale_code', 'product__name')
    readonly_fields = ('created_at',)


class PurchaseReturnAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('return_code', 'date', 'supplier_name', 'supplier_mobile', 'total_amount', 'refund_amount', 'due_amount', 'organization', 'branch', 'created_at')
    list_filter = ('organization', 'branch', 'date', 'created_at')
    search_fields = ('return_code', 'supplier_name', 'supplier_mobile')
    readonly_fields = ('created_at',)
    inlines = [PurchaseReturnItemInline]


class PurchaseReturnItemAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('purchase_return', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'created_at')
    search_fields = ('purchase_return__return_code', 'product__name')
    readonly_fields = ('created_at',)


class SaleReturnAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('return_code', 'date', 'customer_name', 'customer_mobile', 'total_amount', 'refund_amount', 'due_amount', 'organization', 'branch', 'created_at')
    list_filter = ('organization', 'branch', 'date', 'created_at')
    search_fields = ('return_code', 'customer_name', 'customer_mobile')
    readonly_fields = ('created_at',)
    inlines = [SaleReturnItemInline]


class SaleReturnItemAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('sale_return', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'quantity', 'unit_price', 'subtotal', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'created_at')
    search_fields = ('sale_return__return_code', 'product__name')
    readonly_fields = ('created_at',)


class ProductRejectAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ('reject_code', 'date', 'organization', 'branch', 'category', 'product_group', 'brand', 'product', 'reason', 'quantity', 'created_at')
    list_filter = ('organization', 'branch', 'category', 'product_group', 'brand', 'reason', 'date', 'created_at')
    search_fields = ('reject_code', 'product__name')
    readonly_fields = ('created_at',)


@admin.register(StockReservation)
class StockReservationAdmin(TenantScopedAdminMixin, admin.ModelAdmin):
    list_display = ['product', 'session_key', 'reserved_quantity', 'expires_at', 'organization']
    list_filter = ['organization']


# ==========================================================
# REGISTER MODELS (grouped)
# ==========================================================
admin.site.register(OpeningStock, OpeningStockAdmin)
admin.site.register(Purchase, PurchaseAdmin)
admin.site.register(PurchaseItem, PurchaseItemAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem, SaleItemAdmin)
admin.site.register(PurchaseReturn, PurchaseReturnAdmin)
admin.site.register(PurchaseReturnItem, PurchaseReturnItemAdmin)
admin.site.register(SaleReturn, SaleReturnAdmin)
admin.site.register(SaleReturnItem, SaleReturnItemAdmin)
admin.site.register(ProductReject, ProductRejectAdmin)
