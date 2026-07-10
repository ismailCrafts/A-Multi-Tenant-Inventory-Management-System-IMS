from django.contrib import admin
from authenticate_app.models import Branch

def is_platform_superadmin(user) -> bool:
    """
    Helper to determine platform-level superadmin status.

    Steps:
    1. Check Django's is_superuser flag.
    2. Ensure the user is not tied to any organization (organization is None).
    3. Return True only when both conditions are met.
    """
    return user.is_superuser and user.organization is None


class TenantScopedAdminMixin(admin.ModelAdmin):
    """
    Tenant-aware admin mixin to enforce per-tenant scoping and form behavior.

    Behavior (step-by-step):

    1) Queryset scoping:
       - Platform superadmin: sees all records (no filtering).
       - Tenant user: queryset filtered to user's organization; if the model has a branch
         field and the user has a branch, further filter by branch.

    2) Auto-assignment on save:
       - Tenant user: the object's organization is forced to the user's organization before save.
       - Branch remains editable by the tenant user (dropdown is scoped separately).
       - Platform superadmin: no forced assignment; full flexibility.

    3) Hide organization field for tenant users:
       - Organization field is excluded from forms for tenant users so they cannot edit it.
       - Platform superadmin sees the organization field as normal.

    4) Scoped foreign key dropdowns:
       - Tenant users: branch dropdown is limited to branches belonging to their organization;
         organization field is prefilled and disabled.
       - Platform superadmin: sees global dropdowns for foreign keys.
    """

    # 1) Queryset scoping
    def get_queryset(self, request):
        """
        Return a queryset scoped to the requesting user.

        Steps:
        - Obtain base queryset from parent.
        - If the user is a platform superadmin, return the full queryset.
        - Otherwise, filter by the user's organization.
        - If the model supports branch and the user has a branch, filter by branch as well.
        """
        qs = super().get_queryset(request)
        user = request.user

        # Platform-level superadmins see everything
        if is_platform_superadmin(user):
            return qs

        # Tenant users: restrict to their organization
        qs = qs.filter(organization=user.organization)

        # If the model has a branch relation and the user is scoped to a branch, apply branch filter
        if hasattr(qs.model, "branch") and user.branch:
            qs = qs.filter(branch=user.branch)

        return qs

    # 2) Auto-assign org only
    def save_model(self, request, obj, form, change):
        """
        Ensure tenant objects are assigned to the tenant's organization on save.

        Steps:
        - If the user is not a platform superadmin, set obj.organization to the user's organization.
        - Leave branch editable (tenant users can choose branch from scoped dropdown).
        - Call parent save_model to persist the object.
        """
        user = request.user

        # For tenant users, force the organization to their own org before saving
        if not is_platform_superadmin(user):
            obj.organization = user.organization
            # Branch is intentionally not forced here; it remains editable

        # Persist using the default admin save behavior
        super().save_model(request, obj, form, change)

    # 3) Hide org field for tenant users
    def get_exclude(self, request, obj=None):
        """
        Exclude the organization field from admin forms for tenant users.

        Steps:
        - If the user is a tenant user, build an exclusion list that includes 'organization'
          (only if the model actually defines that field).
        - Return the exclusion tuple to hide the field in the admin form.
        - Platform superadmins receive the default exclusion behavior.
        """
        if not is_platform_superadmin(request.user):
            # Start with any exclusions defined by parent
            exclude = list(super().get_exclude(request, obj) or [])

            # Only exclude if the model actually has an 'organization' field
            if "organization" in [f.name for f in self.model._meta.fields]:
                exclude.append("organization")

            # Return a deduplicated tuple of excluded fields
            return tuple(set(exclude))

        # Platform superadmin: no special exclusions
        return super().get_exclude(request, obj)

    # 4) Scoped FK dropdowns
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Scope foreign key form fields for tenant users.

        Steps:
        - For tenant users:
          * Prefill and disable the organization field so it cannot be changed.
          * Limit the branch dropdown queryset to branches belonging to the user's organization.
          * Prefill branch if the user has one.
        - For platform superadmins: leave kwargs untouched for global lists.
        - Call parent implementation to build the form field.
        """
        user = request.user

        if not is_platform_superadmin(user):
            # Prefill and disable organization field so tenant users cannot change it
            if db_field.name == "organization":
                kwargs["initial"] = user.organization
                kwargs["disabled"] = True

            # Scope branch dropdown to the tenant's branches and prefill if available
            if db_field.name == "branch":
                kwargs["queryset"] = Branch.objects.filter(organization=user.organization)
                if user.branch:
                    kwargs["initial"] = user.branch

        # Delegate to parent to construct the actual form field
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
