# ==========================================================
# File: authenticate_app/admin.py
# ==========================================================
from django.contrib import admin
from .models import Organization, Branch, User, LoginHistory, OrganizationRequest
from .services import approve_organization_request, reject_organization_request


# ==========================================================
# LOGIN HISTORY ADMIN
# ==========================================================
@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for LoginHistory model.

    Features:
    - Displays user, IP address, and timestamp in the list view.
    - Provides filters for user, IP, and timestamp for quick auditing.
    - Enables search by username and IP address.
    - Restricts queryset to the current tenant's organization for non-superusers.
    """
    # Columns shown in the admin list view
    list_display = ('user', 'ip_address', 'timestamp')

    # Sidebar filters for narrowing down records
    list_filter = ('user', 'ip_address', 'timestamp')

    # Search functionality for quick lookup
    search_fields = ('user__username', 'ip_address')

    def get_queryset(self, request):
        """
        Override queryset to enforce tenant scoping:
        - Superusers see all login history.
        - Tenant admins only see login history for their organization.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Restrict to current user's organization
            return qs.filter(user__organization=request.user.organization)
        return qs


# ==========================================================
# ORGANIZATION ADMIN
# ==========================================================
class OrganizationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Organization model.

    Features:
    - Displays name, code, and creation date.
    - Enables search by name and code.
    - Restricts queryset to the current tenant's organization for non-superusers.
    """
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

    def get_queryset(self, request):
        """
        Override queryset to enforce tenant scoping:
        - Superusers see all organizations.
        - Tenant admins only see their own organization.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Restrict to the organization of the logged-in tenant admin
            return qs.filter(pk=request.user.organization_id)
        return qs


# ==========================================================
# ORGANIZATION REQUEST ADMIN
# ==========================================================
@admin.register(OrganizationRequest)
class OrganizationRequestAdmin(admin.ModelAdmin):
    """
    Admin configuration for OrganizationRequest model.

    Features:
    - Displays requested name, admin username/email, branch, status, and audit timestamps.
    - Enables search by requested name, admin username, and email.
    - Provides actions to approve or reject pending requests.
    - Marks audit-related fields as read-only.
    """
    list_display = (
        'requested_name',
        'admin_username',
        'admin_email',
        'branch_name',
        'status',
        'created_at',
        'approved_at',
        'rejected_at',
    )
    list_filter = ('status',)
    search_fields = ('requested_name', 'admin_username', 'admin_email')
    readonly_fields = ('status', 'created_at', 'approved_at', 'rejected_at')
    actions = ['approve_selected', 'reject_selected']

    def approve_selected(self, request, queryset):
        """
        Custom admin action:
        - Approves all selected pending organization requests.
        - Calls service function `approve_organization_request`.
        - Displays a success message with the count of approved requests.
        """
        updated = 0
        for req in queryset.filter(status='pending'):
            result = approve_organization_request(req.id)
            if 'success' in result:
                updated += 1
        self.message_user(request, f"Approved {updated} organization request(s).")

    def reject_selected(self, request, queryset):
        """
        Custom admin action:
        - Rejects all selected pending organization requests.
        - Calls service function `reject_organization_request`.
        - Displays a success message with the count of rejected requests.
        """
        updated = 0
        for req in queryset.filter(status='pending'):
            result = reject_organization_request(req.id)
            if 'success' in result:
                updated += 1
        self.message_user(request, f"Rejected {updated} organization request(s).")


# ==========================================================
# BRANCH ADMIN
# ==========================================================
class BranchAdmin(admin.ModelAdmin):
    """
    Admin configuration for Branch model.

    Features:
    - Displays branch name, organization, and code.
    - Enables search by branch name and code.
    - Provides filter by organization.
    - Restricts queryset to the current tenant's organization for non-superusers.
    """
    list_display = ('name', 'organization', 'code')
    search_fields = ('name', 'code')
    list_filter = ('organization',)

    def get_queryset(self, request):
        """
        Override queryset to enforce tenant scoping:
        - Superusers see all branches.
        - Tenant admins only see branches belonging to their organization.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Restrict to branches of the logged-in tenant admin's organization
            return qs.filter(organization=request.user.organization)
        return qs


# ==========================================================
# USER ADMIN
# ==========================================================
class UserAdmin(admin.ModelAdmin):
    """
    Admin configuration for User model.

    Features:
    - Displays username, email, organization, branch, role, and status flags.
    - Enables search by username and email.
    - Provides filters for organization, branch, role, and status flags.
    - Restricts queryset to the current tenant's organization for non-superusers.
    """
    list_display = ('username', 'email', 'organization', 'branch', 'role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('organization', 'branch', 'role', 'is_active', 'is_staff')

    def get_queryset(self, request):
        """
        Override queryset to enforce tenant scoping:
        - Superusers see all users.
        - Tenant admins only see users belonging to their organization.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Restrict to users of the logged-in tenant admin's organization
            return qs.filter(organization=request.user.organization)
        return qs


# ==========================================================
# REGISTER MODELS
# ==========================================================
# Register Organization with custom admin configuration
admin.site.register(Organization, OrganizationAdmin)

# Register Branch with custom admin configuration
admin.site.register(Branch, BranchAdmin)

# Register User with custom admin configuration
admin.site.register(User, UserAdmin)
