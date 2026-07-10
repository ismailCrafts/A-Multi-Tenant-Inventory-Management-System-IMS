from django.contrib import messages
from .models import Category, Brand, ProductGroup, Product
from django.core.exceptions import ValidationError


# ==========================================================
# CATEGORY VALIDATION
# ==========================================================
def validate_category_creation(request, name):
    """
    Validates category creation.
    Steps:
    1. Ensure name is provided.
    2. Check uniqueness of name (per organization).
    3. Return True if valid, else False with error message.
    """
    # Step 1: Required field check
    if not name:
        messages.error(request, "Category name is required.")
        return False

    # Step 2: Uniqueness check (multi-tenant safe: filter by org)
    org = request.user.organization
    if Category.objects.filter(name=name, organization=org).exists():
        messages.error(request, "This category name is already used in your organization.")
        return False

    return True


def validate_category_update(request, new_name, category):
    """
    Validates category update.
    Steps:
    1. Check uniqueness of new name (per organization).
    2. Exclude current category from check.
    3. Return True if valid, else False with error message.
    """
    org = request.user.organization
    if Category.objects.filter(name=new_name, organization=org).exclude(pk=category.pk).exists():
        messages.error(request, "This category name is already used in your organization.")
        return False
    return True


# ==========================================================
# BRAND VALIDATION
# ==========================================================
def validate_brand_creation(request, name, code):
    """
    Validates brand creation.
    Steps:
    1. Ensure name and code are provided.
    2. Check uniqueness of name and code (per organization).
    3. Return True if valid, else False with error message.
    """
    # Step 1: Required fields
    if not name:
        messages.error(request, "Brand name is required.")
        return False
    if not code:
        messages.error(request, "Brand code is required.")
        return False

    org = request.user.organization

    # Step 2: Uniqueness checks
    if Brand.objects.filter(name=name, organization=org).exists():
        messages.error(request, "This brand name already exists in your organization.")
        return False
    if Brand.objects.filter(code=code, organization=org).exists():
        messages.error(request, "This brand code already exists in your organization.")
        return False

    return True


def validate_brand_update(request, new_name,  brand):
    """
    Validates brand update.
    Steps:
    1. Ensure new name and code are provided.
    2. Check uniqueness of new name and code (per organization).
    3. Exclude current brand from check.
    4. Return True if valid, else False with error message.
    """
    if not new_name:
        messages.error(request, "Brand name cannot be empty.")
        return False
    

    org = request.user.organization

    if Brand.objects.filter(name=new_name, organization=org).exclude(pk=brand.pk).exists():
        messages.error(request, "This brand name is already used in your organization.")
        return False
    

    return True


# ==========================================================
# PRODUCT GROUP VALIDATION
# ==========================================================
def validate_productgroup_creation(request, name, category_id, brand_id):
    """
    Validates product group creation.
    Steps:
    1. Ensure all required fields are provided.
    2. Return True if valid, else False with error message.
    """
    if not (name and category_id and brand_id):
        messages.error(request, "All required fields must be filled.")
        return False
    return True


def validate_productgroup_update(request, new_name, productgroup):
    """
    Validates product group update.
    Steps:
    1. Check uniqueness of new name (per organization).
    2. Exclude current product group from check.
    3. Return True if valid, else False with error message.
    """
    org = request.user.organization
    if ProductGroup.objects.filter(name=new_name, organization=org).exclude(pk=productgroup.pk).exists():
        messages.error(request, "This Product Group name is already used in your organization.")
        return False
    return True


# ==========================================================
# PRODUCT VALIDATION
# ==========================================================
def validate_product_creation(request, name, category_id, brand_id, group_id):
    """
    Validates product creation.
    Steps:
    1. Ensure all required fields are provided.
    2. Return True if valid, else False with error message.
    """
    if not (name and category_id and brand_id and group_id):
        messages.error(request, "All required fields must be filled.")
        return False
    return True


def validate_product_update(request, new_name, product):
    """
    Validates product update.
    Steps:
    1. Check uniqueness of new name (per organization).
    2. Exclude current product from check.
    3. Return True if valid, else False with error message.
    """
    org = request.user.organization
    if Product.objects.filter(name=new_name, organization=org).exclude(pk=product.pk).exists():
        messages.error(request, "This product name is already used in your organization.")
        return False
    return True
