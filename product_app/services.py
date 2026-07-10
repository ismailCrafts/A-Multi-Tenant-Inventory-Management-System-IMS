from django.shortcuts import get_object_or_404
from django.core.files import File
from django.db.models import Max
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
from .models import Category, Brand, ProductGroup, Product

# ==========================================================
# CODE GENERATOR
# ==========================================================
def generate_code(prefix, model, organization):
    """
    Generates a formatted, incrementing code per organization (e.g., BR-001, PG-002, PR-003).
    """
    last = model.objects.filter(organization=organization).order_by("-id").first()
    if last:
        try:
            number = int(str(last.code).split("-")[-1]) + 1
        except (ValueError, AttributeError):
            number = 1
    else:
        number = 1
    return f"{prefix}-{number:03d}"


# ==========================================================
# CATEGORY SERVICES
# ==========================================================
def create_category(request, name, description=""):
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    return Category.objects.create(
        name=name,
        description=description,
        organization=org,
        branch=branch,
        created_by=request.user,
        updated_by=request.user
    )

def update_category_from_services(request, category, new_name, description=""):
    category.name = new_name
    category.description = description
    category.updated_by = request.user
    category.save()
    return category

def delete_category_from_services(category):
    category.delete()
    return True


# ==========================================================
# BRAND SERVICES
# ==========================================================
def create_brand(request, name, description=""):
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    code   = generate_code("BR", Brand, org)
    return Brand.objects.create(
        name=name,
        code=code,
        description=description,
        organization=org,
        branch=branch,
        created_by=request.user,
        updated_by=request.user
    )

def update_brand_from_services(request, brand, new_name, description=""):
    brand.name = new_name
    brand.description = description
    brand.updated_by = request.user
    brand.save()
    return brand

def delete_brand_from_services(brand):
    brand.delete()
    return True


# ==========================================================
# PRODUCT GROUP SERVICES
# ==========================================================
def create_productgroup(request, name, category_id, brand_id, description=""):
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    code   = generate_code("PG", ProductGroup, org)
    category = get_object_or_404(Category, id=category_id, organization=org)
    brand    = get_object_or_404(Brand, id=brand_id, organization=org)
    return ProductGroup.objects.create(
        name=name,
        code=code,
        category=category,
        brand=brand,
        description=description,
        organization=org,
        branch=branch,
        created_by=request.user,
        updated_by=request.user
    )

def update_productgroup_from_services(request, productgroup, new_name, description=""):
    productgroup.name = new_name
    productgroup.description = description
    productgroup.updated_by = request.user
    productgroup.save()
    return productgroup

def delete_productgroup_from_services(productgroup):
    productgroup.delete()
    return True


# ==========================================================
# PRODUCT SERVICES
# ==========================================================
def create_product(request, name, category_id, brand_id, group_id, description=""):
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)
    code   = generate_code("PR", Product, org)
    category = get_object_or_404(Category, id=category_id, organization=org)
    brand    = get_object_or_404(Brand, id=brand_id, organization=org)
    group    = get_object_or_404(ProductGroup, id=group_id, organization=org)
    return Product.objects.create(
        name=name,
        code=code,
        category=category,
        brand=brand,
        product_group=group,
        description=description,
        organization=org,
        branch=branch,
        created_by=request.user,
        updated_by=request.user
    )

def update_product_from_services(request, product, new_name=None, category_id=None, brand_id=None, group_id=None, description=None):
    if new_name:
        product.name = new_name
    if description is not None:
        product.description = description
    if category_id:
        product.category = get_object_or_404(Category, id=category_id, organization=product.organization)
    if brand_id:
        product.brand = get_object_or_404(Brand, id=brand_id, organization=product.organization)
    if group_id:
        product.product_group = get_object_or_404(ProductGroup, id=group_id, organization=product.organization)
    product.updated_by = request.user
    product.save()
    return product

def delete_product_from_services(product):
    product.delete()
    return True


# ==========================================================
# BARCODE UTILITIES
# ==========================================================
def get_next_barcode_number(start_number=100000):
    max_barcode = Product.objects.filter(barcode_number__regex=r'^\d+$') \
                                 .aggregate(Max('barcode_number'))['barcode_number__max']
    if max_barcode:
        try:
            next_number = int(max_barcode) + 1
        except ValueError:
            next_number = start_number
    else:
        next_number = start_number
    return str(next_number)

def generate_barcode_image(number):
    Code128 = barcode.get_barcode_class('code128')
    code = Code128(number, writer=ImageWriter())
    buffer = BytesIO()
    code.write(buffer)
    return File(buffer, name=f"{number}.png")
