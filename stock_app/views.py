# stock_app/views.py
from decimal import Decimal
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from urllib.parse import unquote

from . import services, validators
from .models import (
    OpeningStock, Purchase, PurchaseItem, Sale, SaleItem,
    PurchaseReturn, PurchaseReturnItem, SaleReturn, SaleReturnItem, ProductReject
)
from product_app.models import Product, Brand, ProductGroup, Category

#  helper function
def get_user_session_key(request):
    """Generate a consistent session key for the current user."""
    if not request.session.session_key:
        request.session.create()
    request.session.modified = True
    return f"u{request.user.id}_{request.session.session_key}"


# ==========================================================
# OPENING STOCK
# ==========================================================

@login_required
def opening_stock_list(request):
    """
    Lists all opening stock entries for the current tenant (org + branch).
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    opening_stocks = OpeningStock.objects.select_related(
        'product_group', 'brand', 'product'
    ).filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_opening_stock.html', {'opening_stocks': opening_stocks})


@login_required
def opening_stock_detail(request, code):
    """
    Shows details for a single opening stock entry scoped to tenant.
    """
    code = unquote(unquote(code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    opening_stock = get_object_or_404(
        OpeningStock, product__code=code, organization=org, branch=branch
    )

    return render(request, 'stock_app/opening_stock_detail.html', {'opening_stock': opening_stock})


@login_required
def add_opening_stock(request):
    """
    Creates an opening stock entry for the current tenant.
    - On POST: validate, create, then redirect.
    - On GET: preload options and render form.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)
    brands = Brand.objects.filter(organization=org)
    productgroups = ProductGroup.objects.filter(organization=org)
    categories = Category.objects.filter(organization=org)
    today = date.today().isoformat()

    if request.method == "POST":
        valid, err = validators.validate_opening_stock(request.POST)
        if not valid:
            messages.error(request, err)
            return render(
                request,
                'stock_app/opening_stock_form.html',
                {'products': products, 'brands': brands, 'productgroups': productgroups, 'categories': categories, 'today': today}
            )

        services.create_opening_stock(request, request.POST)
        return redirect('view_opening_stock')

    return render(
        request,
        'stock_app/opening_stock_form.html',
        {'products': products, 'brands': brands, 'productgroups': productgroups, 'categories': categories, 'today': today}
    )


# ==========================================================
# PURCHASE
# ==========================================================

@login_required
def purchase_list(request):
    """
    Lists purchases for the current tenant with prefetched items.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    purchases = Purchase.objects.prefetch_related('items__product').filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_purchase.html', {'purchases': purchases})


@login_required
def purchase_detail(request, purchase_code):
    """
    Shows details for a single purchase by code scoped to tenant.
    """
    purchase_code = unquote(unquote(purchase_code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    purchase = get_object_or_404(Purchase, purchase_code=purchase_code, organization=org, branch=branch)

    items = purchase.items.select_related('product', 'brand', 'product_group').all()

    return render(request, 'stock_app/purchase_detail.html', {'purchase': purchase, 'items': items})


@login_required
def add_purchase(request):
    """
    Creates a purchase with multiple items for the current tenant.
    - On POST: validate items, create purchase, then redirect.
    - On GET: preload options and next code.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)

    next_code = services.generate_code('PR', Purchase, 'purchase_code', org)
    today = date.today().isoformat()

    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')

        valid, err = validators.validate_items(product_ids, quantities, unit_prices)
        if not valid:
            messages.error(request, err)
            return render(request, 'stock_app/add_purchase.html', {'products': products, 'next_code': next_code, 'today': today})

        items = []
        for i in range(len(product_ids)):
            product = get_object_or_404(Product, id=product_ids[i], organization=org)
            items.append({
                'product': product,
                'group': product.product_group,
                'brand': product.brand,
                'quantity': Decimal(quantities[i]),
                'unit_price': Decimal(unit_prices[i]),
            })

        try:
            services.create_purchase(request, request.POST, items)
            return redirect('view_purchase')
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'stock_app/add_purchase.html', {'products': products, 'next_code': next_code, 'today': today})

    return render(request, 'stock_app/add_purchase.html', {'products': products, 'next_code': next_code, 'today': today})


# ==========================================================
# SALE
# ==========================================================

@login_required
def sale_list(request):
    """
    Lists sales for the current tenant with prefetched items.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    sales = Sale.objects.prefetch_related('items__product').filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_sale.html', {'sales': sales})


@login_required
def sale_detail(request, sale_code):
    """
    Shows details for a single sale by code scoped to tenant.
    """
    sale_code = unquote(unquote(sale_code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    sale = get_object_or_404(Sale, sale_code=sale_code, organization=org, branch=branch)

    items = sale.items.select_related('product', 'brand', 'product_group').all()

    return render(request, 'stock_app/sale_detail.html', {'sale': sale, 'items': items})


@login_required
def add_sale(request):
    """
    Creates a sale with multiple items for the current tenant.
    - On POST: validate items, create sale, then redirect.
    - On GET: preload options and next code.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)

    next_code = services.generate_code('SL', Sale, 'sale_code', org)
    today = date.today().isoformat()

    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')

        valid, err = validators.validate_items(product_ids, quantities, unit_prices)
        if not valid:
            messages.error(request, err)
            return render(request, 'stock_app/add_sale.html', {'products': products, 'next_code': next_code, 'today': today})

        items = []
        for i in range(len(product_ids)):
            product = get_object_or_404(Product, id=product_ids[i], organization=org)
            items.append({
                'product': product,
                'group': product.product_group,
                'brand': product.brand,
                'quantity': Decimal(quantities[i]),
                'unit_price': Decimal(unit_prices[i]),
            })

        try:
            services.create_sale(request, request.POST, items)
            return redirect('view_sale')
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'stock_app/add_sale.html', {'products': products, 'next_code': next_code, 'today': today})

    return render(request, 'stock_app/add_sale.html', {'products': products, 'next_code': next_code, 'today': today})


# ==========================================================
# PURCHASE RETURN
# ==========================================================

@login_required
def purchase_return_list(request):
    """
    Lists purchase returns for the current tenant with prefetched items.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    returns = PurchaseReturn.objects.prefetch_related('items__product').filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_purchase_return.html', {'returns': returns})


@login_required
def purchase_return_detail(request, return_code):
    """
    Shows details for a single purchase return by code scoped to tenant.
    """
    return_code = unquote(unquote(return_code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    pr = get_object_or_404(PurchaseReturn, return_code=return_code, organization=org, branch=branch)

    items = pr.items.select_related('product').all()

    return render(request, 'stock_app/purchase_return_detail.html', {'pr': pr, 'items': items})


@login_required
def add_purchase_return(request):
    """
    Creates a purchase return with multiple items for the current tenant.
    - On POST: validate items, create purchase return, then redirect.
    - On GET: preload options and next code.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)

    next_code = services.generate_code('PRR', PurchaseReturn, 'return_code', org)
    today = date.today().isoformat()

    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')

        valid, err = validators.validate_items(product_ids, quantities, unit_prices)
        if not valid:
            messages.error(request, err)
            return render(request, 'stock_app/add_purchase_return.html', {'products': products, 'next_code': next_code, 'today': today})

        items = []
        for i in range(len(product_ids)):
            product = get_object_or_404(Product, id=product_ids[i], organization=org)
            items.append({
                'product': product,
                'group': product.product_group,
                'brand': product.brand,
                'quantity': Decimal(quantities[i]),
                'unit_price': Decimal(unit_prices[i]),
            })

        try:
            services.create_purchase_return(request, request.POST, items)
            return redirect('view_purchase_return')
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'stock_app/add_purchase_return.html', {'products': products, 'next_code': next_code, 'today': today})

    return render(request, 'stock_app/add_purchase_return.html', {'products': products, 'next_code': next_code, 'today': today})


# ==========================================================
# SALE RETURN
# ==========================================================

@login_required
def sale_return_list(request):
    """
    Lists sale returns for the current tenant with prefetched items.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    sale_returns = SaleReturn.objects.prefetch_related('items__product').filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_sale_return.html', {'sale_returns': sale_returns})


@login_required
def sale_return_detail(request, return_code):
    """
    Shows details for a single sale return by code scoped to tenant.
    """
    return_code = unquote(unquote(return_code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    sr = get_object_or_404(SaleReturn, return_code=return_code, organization=org, branch=branch)

    items = sr.items.select_related('product').all()

    return render(request, 'stock_app/sale_return_detail.html', {'sr': sr, 'items': items})


@login_required
def add_sale_return(request):
    """
    Creates a sale return with multiple items for the current tenant.
    - On POST: validate items, create sale return, then redirect.
    - On GET: preload options and next code.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)

    next_code = services.generate_code('SRR', SaleReturn, 'return_code', org)
    today = date.today().isoformat()

    if request.method == "POST":
        product_ids = request.POST.getlist('product_ids[]')
        quantities = request.POST.getlist('quantities[]')
        unit_prices = request.POST.getlist('unit_prices[]')

        valid, err = validators.validate_items(product_ids, quantities, unit_prices)
        if not valid:
            messages.error(request, err)
            return render(request, 'stock_app/add_sale_return.html', {'products': products, 'next_code': next_code, 'today': today})

        items = []
        for i in range(len(product_ids)):
            product = get_object_or_404(Product, id=product_ids[i], organization=org)
            items.append({
                'product': product,
                'group': product.product_group,
                'brand': product.brand,
                'quantity': Decimal(quantities[i]),
                'unit_price': Decimal(unit_prices[i]),
            })

        try:
            services.create_sale_return(request, request.POST, items)
            return redirect('view_sale_return')
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'stock_app/add_sale_return.html', {'products': products, 'next_code': next_code, 'today': today})

    return render(request, 'stock_app/add_sale_return.html', {'products': products, 'next_code': next_code, 'today': today})


# ==========================================================
# PRODUCT REJECT
# ==========================================================

@login_required
def reject_list(request):
    """
    Lists product rejects for the current tenant with related product/group/brand.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    rejects = ProductReject.objects.select_related('product', 'brand', 'product_group').filter(organization=org, branch=branch)

    return render(request, 'stock_app/view_reject.html', {'rejects': rejects})


@login_required
def reject_detail(request, reject_code):
    """
    Shows details for a single product reject scoped to tenant.
    """
    reject_code = unquote(unquote(reject_code))
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    reject = get_object_or_404(ProductReject, reject_code=reject_code, organization=org, branch=branch)

    return render(request, 'stock_app/reject_detail.html', {'reject': reject})


@login_required
def add_reject(request):
    """
    Creates a product reject entry for the current tenant.
    - On POST: validate, create, then redirect.
    - On GET: preload options, purchases, and next code.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    products = Product.objects.filter(organization=org)
    for p in products:
        p.current_stock = services.get_current_stock(p, org, branch)

    reasons = ProductReject.REJECT_REASONS
    next_code = services.generate_code('RJ', ProductReject, 'reject_code', org)
    today = date.today().isoformat()
    purchases = Purchase.objects.filter(organization=org, branch=branch)

    if request.method == "POST":
        valid, err = validators.validate_reject(request.POST)
        if not valid:
            messages.error(request, err)
            return render(request, 'stock_app/add_reject.html', {
                'products': products,
                'reasons': reasons,
                'next_code': next_code,
                'today': today,
                'purchases': purchases,
            })

        try:
            services.create_reject(request, request.POST)
            return redirect('view_reject')
        except ValidationError as e:
            messages.error(request, str(e))
            return render(request, 'stock_app/add_reject.html', {
                'products': products,
                'reasons': reasons,
                'next_code': next_code,
                'today': today,
                'purchases': purchases,
            })

    return render(request, 'stock_app/add_reject.html', {
        'products': products,
        'reasons': reasons,
        'next_code': next_code,
        'today': today,
        'purchases': purchases,
    })


# ==========================================================
# Barcode lookup for stock forms
# ==========================================================

@login_required
def stock_lookup_by_barcode(request):
    """
    Look up a product by barcode number OR product code and return product metadata,
    current stock, and latest price suggestion for this org/branch.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    barcode = request.GET.get("barcode", "").strip()
    if not barcode:
        return JsonResponse({"error": "Barcode required"}, status=400)

    product = services.get_product_by_barcode(barcode, org)
    if not product:
        from product_app.models import Product as ProductModel
        product = (
            ProductModel.objects
            .select_related("category", "brand", "product_group")
            .filter(code__iexact=barcode, organization=org)
            .first()
        )
    if not product:
        return JsonResponse({"error": "Product not found"}, status=404)

    if getattr(product, 'organization', None) != org:
        return JsonResponse({"error": "Product not found"}, status=404)

    current_stock = services.get_current_stock(product, org, branch)
    suggested_price = services.get_latest_price(product, org, branch)

    if not request.session.session_key:
        request.session.create()
    request.session.modified = True
    raw_key = request.session.session_key or 'nosession'
    session_key = f"u{request.user.id}_{raw_key}"
    services.cleanup_expired_reservations(organization=org, branch=branch)
    available_stock = services.get_available_stock(product, org, branch, session_key=session_key)

    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "category": product.category.name if product.category else None,
        "brand": product.brand.name if product.brand else None,
        "group": product.product_group.name if product.product_group else None,
        "barcode_number": product.barcode_number,
        "current_stock": current_stock,
        "available_stock": available_stock,
        "suggested_price": str(suggested_price) if suggested_price is not None else None,
    })


@login_required
def low_stock_report(request):
    """
    Tenant-scoped low stock report.
    """
    org = request.user.organization
    branch = getattr(request.user, "branch", None)

    products = Product.objects.filter(organization=org)

    low_stock_products = []
    for p in products:
        current_stock = services.get_current_stock(p, org, branch)
        if p.low_stock_threshold and current_stock <= p.low_stock_threshold:
            low_stock_products.append({
                "product": p,
                "current_stock": current_stock,
                "threshold": p.low_stock_threshold,
            })

    return render(request, "stock_app/low_stock_report.html", {
        "low_stock_products": low_stock_products
    })


# ==========================================================
# STOCK RESERVATION API
# ==========================================================

@login_required
def stock_reserve(request):
    """
    POST: Reserve or update a quantity for a product in this session.
    GET: Get available stock for a product
    """
    import json

    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    session_key = get_user_session_key(request)

    # GET request - check available stock
    if request.method == 'GET':
        product_id = request.GET.get('product_id')
        if not product_id:
            return JsonResponse({'error': 'product_id required'}, status=400)

        try:
            product = Product.objects.get(id=product_id, organization=org)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

        services.cleanup_expired_reservations(organization=org, branch=branch)

        real_stock = services.get_current_stock(product, org, branch)

        details = services.get_reservation_details(product, org, branch, session_key)

        available = max(0, real_stock - details['others_reserved'])

        return JsonResponse({
            'success': True,
            'real_stock': float(real_stock),
            'available_stock': float(available),
            'total_reserved': float(details['total_reserved']),
            'your_reservation': float(details['your_reservation']),
        })

    # POST request - create/update reservation
    if request.method == 'POST':
        try:
            if request.content_type and 'application/json' in request.content_type:
                body = json.loads(request.body)
            else:
                body = request.POST
            product_id = body.get('product_id')
            quantity = body.get('quantity', 0)
        except (json.JSONDecodeError, Exception) as e:
            return JsonResponse({'error': f'Invalid request body: {str(e)}'}, status=400)

        if not product_id:
            return JsonResponse({'error': 'product_id required'}, status=400)

        try:
            product = Product.objects.get(id=product_id, organization=org)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)

        qty = float(quantity or 0)

        if qty <= 0:
            services.release_reservation(session_key, product, org, branch)

            services.cleanup_expired_reservations(organization=org, branch=branch)
            real_stock = services.get_current_stock(product, org, branch)
            details = services.get_reservation_details(product, org, branch, session_key)
            available = max(0, real_stock - details['others_reserved'])

            return JsonResponse({
                'success': True,
                'real_stock': float(real_stock),
                'available_stock': float(available),
                'your_reservation': 0,
                'message': 'Reservation released.',
            })

        # Set new reservation (pass request.user so created_by/updated_by are recorded)
        result = services.set_reservation(session_key, product, org, branch, qty, user=request.user)

        # Recalculate real/available after reservation attempt
        services.cleanup_expired_reservations(organization=org, branch=branch)
        real_stock = services.get_current_stock(product, org, branch)
        details = services.get_reservation_details(product, org, branch, session_key)
        available = max(0, real_stock - details['others_reserved'])

        response = {
            'success': result.get('success', False),
            'real_stock': float(real_stock),
            'available_stock': float(available),
            'your_reservation': float(result.get('your_reservation', 0)),
            'message': result.get('message', ''),
        }
        if 'available_stock' in result:
            response['service_reported_available_stock'] = result['available_stock']
        if 'real_stock' in result:
            response['service_reported_real_stock'] = result['real_stock']

        return JsonResponse(response)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ==========================================================
# BULK AVAILABLE STOCK (live polling)
# ==========================================================

@login_required
def stock_available_bulk(request):
    """
    Return available stock for multiple products (used for live polling).

    Steps:
    1. Read product ids from query params (supports repeated params or comma-separated).
    2. Resolve tenant organization and branch from request.user.
    3. Fetch products scoped to tenant; ignore ids that don't belong to tenant.
    4. For each product compute current stock via services.get_current_stock.
    5. Return JSON list of {product_id, product_code, name, available}.
    """
    # Step 1: parse product ids from query params
    raw_ids = request.GET.getlist('product_ids')
    if not raw_ids:
        raw = request.GET.get('product_ids', '')
        if raw:
            raw_ids = [p.strip() for p in raw.split(',') if p.strip()]

    if not raw_ids:
        return JsonResponse({'error': 'product_ids parameter is required'}, status=400)

    ids = []
    for v in raw_ids:
        try:
            ids.append(int(v))
        except (ValueError, TypeError):
            continue

    if not ids:
        return JsonResponse({'error': 'No valid product ids provided'}, status=400)

    # Step 2: tenant context
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 3: fetch products scoped to tenant
    products = Product.objects.filter(id__in=ids, organization=org)
    found_ids = set(p.id for p in products)

    results = []
    for product in products:
        # Step 4: compute current stock using existing service
        try:
            available = services.get_current_stock(product, org, branch)
        except Exception:
            available = None

        results.append({
            'product_id': product.id,
            'product_code': product.code,
            'name': product.name,
            'available': available,
        })

    missing = [pid for pid in ids if pid not in found_ids]
    response = {'results': results}
    if missing:
        response['missing_product_ids'] = missing

    return JsonResponse(response, status=200)


# ==========================================================
# DEBUG VIEW (optional)
# ==========================================================

@login_required
def stock_debug(request):
    """
    Simple debug endpoint to inspect reservation state for a product or session.
    Intended for development; remove or protect in production.
    """
    org = request.user.organization
    branch = getattr(request.user, 'branch', None)

    product_id = request.GET.get('product_id')
    session_key = request.GET.get('session_key') or get_user_session_key(request)

    data = {
        'product_id': product_id,
        'session_key': session_key,
        'reservations': None,
        'cleanup_result': None,
    }

    try:
        services.cleanup_expired_reservations(organization=org, branch=branch)
        data['cleanup_result'] = True
    except Exception as e:
        data['cleanup_result'] = f"cleanup error: {str(e)}"

    if product_id:
        try:
            product = Product.objects.get(id=product_id, organization=org)
            details = services.get_reservation_details(product, org, branch, session_key)
            data['reservations'] = details
        except Product.DoesNotExist:
            data['reservations'] = 'product not found'
        except Exception as e:
            data['reservations'] = f"error: {str(e)}"

    return JsonResponse(data)
