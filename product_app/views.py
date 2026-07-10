from django.shortcuts import render, redirect, get_object_or_404
from urllib.parse import unquote
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Brand, ProductGroup, Product, Category
from .validators import (
    validate_category_creation,
    validate_category_update,
    validate_brand_creation,
    validate_brand_update,
    validate_productgroup_creation,
    validate_productgroup_update,
    validate_product_creation,
    validate_product_update,
)
from .services import (
    create_category,
    update_category_from_services,
    delete_category_from_services,
    create_brand,
    update_brand_from_services,
    delete_brand_from_services,
    create_productgroup,
    update_productgroup_from_services,
    delete_productgroup_from_services,
    create_product,
    update_product_from_services,
    delete_product_from_services,
    generate_code,
    get_next_barcode_number,
    generate_barcode_image,
)
from stock_app.services import get_current_stock


# ==========================================================
# CATEGORY VIEWS (no code generation or code fields)
# ==========================================================

@login_required
def view_category(request):
    """
    List categories scoped to the logged-in user's organization and branch.

    Steps:
    1. Resolve the current user's organization and optional branch.
    2. Query Category objects filtered by organization and branch.
    3. Render the category list template with the queryset.
    """
    # Step 1: Tenant context from authenticated user
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Fetch categories scoped to tenant context
    categories = Category.objects.filter(organization=org, branch=branch)

    # Step 3: Render list view
    return render(request, 'product_app/view_category.html', {'categories': categories})


@login_required
def add_category(request):
    """
    Create a new category for the user's organization/branch.

    Steps:
    1. On GET: render the creation form.
    2. On POST: extract form inputs.
    3. Validate inputs using validators.
    4. Delegate creation to service layer (service will set created_by/updated_by).
    5. Provide user feedback and redirect to category list.
    """
    # Step 1: Render form for non-POST requests
    if request.method == 'POST':
        # Step 2: Form inputs
        name = request.POST.get('category_name')
        description = request.POST.get('category_description')

        # Step 3: Validate creation inputs
        if not validate_category_creation(request, name):
            return redirect('add_category')

        # Step 4: Create category via service (service handles audit fields)
        create_category(request, name, description=description)

        # Step 5: Feedback and redirect
        messages.success(request, "Category added successfully.")
        return redirect('view_category')

    # GET: render form
    return render(request, 'product_app/add_category.html')


@login_required
def category_detail(request, name):
    """
    Display details for a single category by name within the tenant.

    Steps:
    1. Resolve tenant organization.
    2. Retrieve Category by name and organization (404 if not found).
    3. Render detail template with the category instance.
    """
    name = unquote(unquote(name))  # Decode URL-encoded name (handles %20 and %2520)
    # Step 1: Tenant context
    org = request.user.organization

    # Step 2: Safe retrieval scoped to org
    category = get_object_or_404(Category, name=name, organization=org)

    # Step 3: Render detail view
    return render(request, "product_app/category_detail.html", {"category": category})


@login_required
def update_category(request, name):
    """
    Update an existing category scoped to the tenant.

    Steps:
    1. Resolve tenant organization and fetch category by name.
    2. On POST: extract inputs and validate update.
    3. Delegate update to service layer and persist changes (service sets updated_by).
    4. Provide feedback and redirect to list.
    5. On GET: render prefilled update form.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and fetch category
    org = request.user.organization
    category = get_object_or_404(Category, name=name, organization=org)

    if request.method == 'POST':
        # Step 2: Extract inputs
        new_name = request.POST.get('category_name')
        description = request.POST.get('category_description')

        # Step 3: Validate update
        if not validate_category_update(request, new_name, category):
            return redirect('update_category', name=category.name)

        # Step 4: Delegate update to service (service will set updated_by)
        update_category_from_services(request, category, new_name, description)
        messages.success(request, "Category updated successfully.")
        return redirect('view_category')

    # GET: Render update form
    return render(request, 'product_app/update_category.html', {'category': category})


@login_required
def delete_category(request, name):
    """
    Delete a category by name within the tenant.

    Steps:
    1. Resolve tenant organization and fetch category.
    2. Delegate deletion to service layer.
    3. Provide feedback and redirect to category list.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and safe fetch
    org = request.user.organization
    category = get_object_or_404(Category, name=name, organization=org)

    # Step 2: Delete via service
    delete_category_from_services(category)

    # Step 3: Feedback and redirect
    messages.success(request, f"Category '{name}' deleted successfully")
    return redirect('view_category')


# ==========================================================
# BRAND VIEWS (auto-generated code, prefilled on add)
# ==========================================================

@login_required
def view_brand(request):
    """
    List brands scoped to the user's organization and branch.

    Steps:
    1. Resolve tenant context.
    2. Query Brand objects filtered by organization and branch.
    3. Render the brand list template.
    """
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Fetch brands scoped to tenant
    brands = Brand.objects.filter(organization=org, branch=branch)

    # Step 3: Render list view
    return render(request, 'product_app/view_brand.html', {'brands': brands})


@login_required
def add_brand(request):
    """
    Create a brand with an auto-generated code (prefilled in the form).

    Steps:
    1. Resolve tenant context.
    2. On GET: generate next code and render form with prefilled code.
    3. On POST: validate inputs and delegate creation to service.
    4. Provide feedback and redirect to brand list.
    """
    # Step 1: Tenant context
    org = request.user.organization

    if request.method == 'POST':
        # Step 3: Extract inputs from form
        name = request.POST.get('brand_name')
        description = request.POST.get('brand_description')
        code = request.POST.get('code')

        # Step 3: Validate creation inputs
        if not validate_brand_creation(request, name, code):
            return redirect('add_brand')

        # Step 4: Create brand via service (service will generate code and set audit fields)
        create_brand(request, name, description=description)
        messages.success(request, "Brand added successfully.")
        return redirect('view_brand')

    # GET: Prefill next code for display (readonly in form)
    next_code = generate_code("BR", Brand, organization=org)
    return render(request, 'product_app/add_brand.html', {'next_code': next_code})


@login_required
def brand_detail(request, name):
    """
    Show details for a single brand by name within the tenant.

    Steps:
    1. Resolve tenant organization.
    2. Retrieve Brand by name and organization.
    3. Render detail template with the brand instance.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context
    org = request.user.organization

    # Step 2: Safe retrieval scoped to org
    brand = get_object_or_404(Brand, name=name, organization=org)

    # Step 3: Render detail view
    return render(request, "product_app/brand_detail.html", {"brand": brand})


@login_required
def update_brand(request, name):
    """
    Update a brand scoped to the tenant.

    Steps:
    1. Resolve tenant organization and fetch brand by name.
    2. On POST: extract inputs and validate update.
    3. Delegate update to service layer and persist changes (service sets updated_by).
    4. Provide feedback and redirect to brand list.
    5. On GET: render prefilled update form.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and fetch brand
    org = request.user.organization
    brand = get_object_or_404(Brand, name=name, organization=org)

    if request.method == 'POST':
        # Step 2: Extract inputs
        new_name = request.POST.get('new_name')
        description = request.POST.get('brand_description')

        # Step 3: Validate update
        if not validate_brand_update(request, new_name, brand):
            return redirect('update_brand', name=brand.name)

        # Step 4: Delegate update to service
        update_brand_from_services(request, brand, new_name, description)
        messages.success(request, "Brand updated successfully.")
        return redirect('view_brand')

    # GET: Render update form
    return render(request, 'product_app/update_brand.html', {'brand': brand})


@login_required
def delete_brand(request, name):
    """
    Delete a brand by name within the tenant.

    Steps:
    1. Resolve tenant organization and fetch brand.
    2. Delegate deletion to service layer.
    3. Provide feedback and redirect to brand list.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and safe fetch
    org = request.user.organization
    brand = get_object_or_404(Brand, name=name, organization=org)

    # Step 2: Delete via service
    delete_brand_from_services(brand)

    # Step 3: Feedback and redirect
    messages.success(request, f"Brand '{brand.name}' deleted successfully.")
    return redirect("view_brand")


# ==========================================================
# PRODUCT GROUP VIEWS (auto-generated code, prefilled on add)
# ==========================================================

@login_required
def view_productgroup(request):
    """
    List product groups scoped to the user's organization and branch, including related category and brand.

    Steps:
    1. Resolve tenant context.
    2. Query ProductGroup objects with select_related for relations.
    3. Render the product group list template.
    """
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Fetch product groups with related objects for efficiency
    productgroups = ProductGroup.objects.select_related('category', 'brand') \
                                        .filter(organization=org, branch=branch)

    # Step 3: Render list view
    return render(request, 'product_app/view_productgroup.html', {'productgroups': productgroups})


@login_required
def add_productgroup(request):
    """
    Create a product group with an auto-generated code (prefilled).

    Steps:
    1. Resolve tenant context.
    2. On GET: generate next PG code and preload categories/brands for the form.
    3. On POST: validate inputs and delegate creation to service.
    4. Provide feedback and redirect to product group list.
    """
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    if request.method == 'POST':
        # Step 3: Extract inputs from form
        name = request.POST.get('group_name')
        category_id = request.POST.get('group_category')
        brand_id = request.POST.get('group_brand')
        description = request.POST.get('group_description')

        # Step 3: Validate creation inputs
        if not validate_productgroup_creation(request, name, category_id, brand_id):
            return redirect('add_productgroup')

        # Step 4: Create product group via service (service handles audit)
        create_productgroup(request, name, category_id, brand_id, description=description)
        messages.success(request, "Product group added successfully.")
        return redirect('view_productgroup')

    # GET: Prefill next code and preload related options for GET
    next_code = generate_code("PG", ProductGroup, org)
    categories = Category.objects.filter(organization=org, branch=branch)
    brands = Brand.objects.filter(organization=org, branch=branch)
    return render(request, 'product_app/add_productgroup.html', {
        'next_code': next_code,
        'categories': categories,
        'brands': brands
    })


@login_required
def productgroups_detail(request, name):
    """
    Show details for a single product group by name within the tenant.

    Steps:
    1. Resolve tenant organization.
    2. Retrieve ProductGroup by name and organization.
    3. Render detail template with the product group instance.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context
    org = request.user.organization

    # Step 2: Safe retrieval scoped to org
    productgroup = get_object_or_404(ProductGroup, name=name, organization=org)

    # Step 3: Render detail view
    return render(request, "product_app/productgroup_detail.html", {"productgroup": productgroup})


@login_required
def update_productgroup(request, name):
    """
    Update a product group scoped to the tenant.

    Steps:
    1. Resolve tenant organization and fetch product group by name.
    2. On POST: extract inputs and validate update.
    3. Delegate update to service layer and persist changes (service sets updated_by).
    4. Provide feedback and redirect to product group list.
    5. On GET: render prefilled update form.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and fetch product group
    org = request.user.organization
    productgroup = get_object_or_404(ProductGroup, name=name, organization=org)

    if request.method == 'POST':
        # Step 2: Extract inputs
        new_name = request.POST.get('productgroup_name')
        description = request.POST.get('productgroup_description')

        # Step 3: Validate update
        if not validate_productgroup_update(request, new_name, productgroup):
            return redirect('update_productgroup', name=productgroup.name)

        # Step 4: Delegate update to service
        update_productgroup_from_services(request, productgroup, new_name, description)
        messages.success(request, 'Product group updated successfully.')
        return redirect('view_productgroup')

    # GET: Render update form
    return render(request, 'product_app/update_productgroup.html', {'productgroup': productgroup})


@login_required
def delete_productgroup(request, name):
    """
    Delete a product group by name within the tenant.

    Steps:
    1. Resolve tenant organization and fetch product group.
    2. Delegate deletion to service layer.
    3. Provide feedback and redirect to product group list.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and safe fetch
    org = request.user.organization
    productgroup = get_object_or_404(ProductGroup, name=name, organization=org)

    # Step 2: Delete via service
    delete_productgroup_from_services(productgroup)

    # Step 3: Feedback and redirect
    messages.success(request, f"Product group '{productgroup.name}' deleted successfully.")
    return redirect("view_productgroup")


# ==========================================================
# PRODUCT VIEWS (auto-generated code + barcode)
# ==========================================================

@login_required
def view_product(request):
    """
    List products scoped to the user's organization and branch, including related category, brand, and group.

    Steps:
    1. Resolve tenant context.
    2. Query Product objects with select_related for relations.
    3. Render the product list template.
    """
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Fetch products with related objects for efficiency
    products = Product.objects.select_related('category', 'brand', 'product_group') \
                              .filter(organization=org, branch=branch)

    # Step 3: Render list view
    return render(request, 'product_app/view_product.html', {'products': products})


@login_required
def add_product(request):
    """
    Create a product with auto-generated code and barcode image.

    Steps:
    1. Resolve tenant context.
    2. On GET: generate next PR code and preload options for the form.
    3. On POST: validate inputs and create product via service.
    4. Generate a unique numeric barcode and barcode image.
    5. Attach barcode image to product and save.
    6. Provide feedback and redirect to product list.
    """
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    if request.method == 'POST':
        # Step 3: Extract inputs from form
        name = request.POST.get('product_name')
        category_id = request.POST.get('product_category')
        brand_id = request.POST.get('product_brand')
        group_id = request.POST.get('product_group')
        description = request.POST.get('product_description')

        # Step 3: Validate creation inputs
        if not validate_product_creation(request, name, category_id, brand_id, group_id):
            return redirect('add_product')

        # Step 4: Generate next numeric barcode number
        barcode_number = get_next_barcode_number()

        # Step 5: Create product via service (service will generate code and set audit fields)
        product = create_product(request, name, category_id, brand_id, group_id, description=description)

        # Step 6: Attach barcode number and generate image, then save to ImageField
        product.barcode_number = barcode_number
        barcode_file = generate_barcode_image(barcode_number)
        product.barcode_image.save(f"{barcode_number}.png", barcode_file, save=True)

        # Step 7: Feedback and redirect
        messages.success(request, "Product added successfully.")
        return redirect('view_product')

    # GET: Prefill next product code and preload related options for GET
    next_code = generate_code("PR", Product, org)
    categories = Category.objects.filter(organization=org, branch=branch)
    brands = Brand.objects.filter(organization=org, branch=branch)
    productgroups = ProductGroup.objects.filter(organization=org, branch=branch)
    return render(request, 'product_app/add_product.html', {
        'next_code': next_code,
        'categories': categories,
        'brands': brands,
        'productgroups': productgroups
    })


@login_required
def product_detail(request, name):
    """
    Show details for a single product within the tenant, including current stock.

    Steps:
    1. Resolve tenant context.
    2. Retrieve Product by name and organization.
    3. Compute current stock via stock service.
    4. Render detail template with product and stock information.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Safe retrieval scoped to org
    product = get_object_or_404(Product, name=name, organization=org)

    # Step 3: Compute current stock using stock service
    current_stock = get_current_stock(product, org, branch)

    # Step 4: Render detail view with stock
    return render(request, "product_app/product_detail.html", {
        "product": product,
        "current_stock": current_stock,
    })


@login_required
def update_product(request, name):
    """
    Update a product scoped to the tenant.

    Steps:
    1. Resolve tenant context and fetch product by name.
    2. On GET: preload categories/brands/productgroups and render prefilled form.
    3. On POST: extract inputs and validate update.
    4. Delegate update to service layer (service sets updated_by).
    5. Provide feedback and redirect to product list.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and fetch product
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)
    product = get_object_or_404(Product, name=name, organization=org)

    if request.method != 'POST':
        # Step 2: Render prefilled form for non-POST requests
        categories = Category.objects.filter(organization=org, branch=branch)
        brands = Brand.objects.filter(organization=org, branch=branch)
        productgroups = ProductGroup.objects.filter(organization=org, branch=branch)
        return render(request, 'product_app/update_product.html', {
            'product': product,
            'categories': categories,
            'brands': brands,
            'productgroups': productgroups
        })

    # POST handling
    # Step 3: Extract inputs from POST
    new_name = request.POST.get('product_name')
    description = request.POST.get('product_description')
    category_id = request.POST.get('product_category')
    brand_id = request.POST.get('product_brand')
    group_id = request.POST.get('product_group')

    # Step 4: Validate update inputs
    if not validate_product_update(request, new_name, product):
        return redirect('update_product', name=product.name)

    # Step 5: Delegate update to service (service will set updated_by)
    update_product_from_services(request, product, new_name, category_id, brand_id, group_id, description)
    messages.success(request, 'Product updated successfully.')
    return redirect('view_product')


@login_required
def delete_product(request, name):
    """
    Delete a product by name within the tenant.

    Steps:
    1. Resolve tenant organization and fetch product.
    2. Delegate deletion to service layer.
    3. Provide feedback and redirect to product list.
    """
    name = unquote(unquote(name))
    # Step 1: Tenant context and safe fetch
    org = request.user.organization
    product = get_object_or_404(Product, name=name, organization=org)

    # Step 2: Delete via service
    delete_product_from_services(product)

    # Step 3: Feedback and redirect
    messages.success(request, f"Product '{product.name}' deleted successfully.")
    return redirect("view_product")