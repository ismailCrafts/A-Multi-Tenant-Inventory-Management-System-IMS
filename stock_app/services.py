# services.py
from decimal import Decimal
from datetime import date as _date
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

# Import models
from .models import (
    OpeningStock,
    Purchase, PurchaseItem,
    Sale, SaleItem,
    PurchaseReturn, PurchaseReturnItem,
    SaleReturn, SaleReturnItem,
    ProductReject,
    StockReservation
)
from product_app.models import Product

# ==========================================================
# CONSTANTS
# ==========================================================
RESERVATION_TTL_MINUTES = 30

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================

def safe_decimal(value, default="0"):
    """Convert value to Decimal safely."""
    if value in (None, ""):
        return Decimal(default)
    return Decimal(str(value))

def safe_date(value):
    """Return a valid date string."""
    return value or _date.today().isoformat()

def _reservation_expiry():
    """Return expiry datetime = now + TTL."""
    return timezone.now() + timedelta(minutes=RESERVATION_TTL_MINUTES)

# ==========================================================
# LOW STOCK ALERT
# ==========================================================

def check_low_stock_alert(request, product, current_stock):
    """Fire a low stock alert when stock <= threshold."""
    threshold = getattr(product, "low_stock_threshold", 0)
    if threshold and current_stock <= threshold:
        messages.warning(request, f"Low stock alert: {product.name} has only {current_stock} left.")
        try:
            send_mail(
                subject=f"Low Stock Alert: {product.name}",
                message=f"{product.name} stock is {current_stock}, below threshold {threshold}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
        except Exception:
            pass

# ==========================================================
# STOCK UTILITIES
# ==========================================================

def get_current_stock(product, organization, branch=None):
    """Return current stock from OpeningStock."""
    stock = OpeningStock.objects.filter(
        organization=organization, branch=branch, product=product
    ).first()
    return float(stock.stock) if stock else 0

def get_latest_price(product, organization, branch=None):
    """Suggest the most recent unit price for this product."""
    latest_purchase = PurchaseItem.objects.filter(
        organization=organization, branch=branch, product=product
    ).order_by("-created_at").first()

    latest_sale = SaleItem.objects.filter(
        organization=organization, branch=branch, product=product
    ).order_by("-created_at").first()

    if latest_purchase and latest_sale:
        return (
            float(latest_sale.unit_price)
            if latest_sale.created_at >= latest_purchase.created_at
            else float(latest_purchase.unit_price)
        )
    if latest_sale:
        return float(latest_sale.unit_price)
    if latest_purchase:
        return float(latest_purchase.unit_price)
    return None

def get_product_by_barcode(barcode_number: str, organization):
    """Lookup product by barcode number."""
    if not barcode_number:
        return None
    return (
        Product.objects.select_related("category", "brand", "product_group")
        .filter(barcode_number=barcode_number, organization=organization)
        .first()
    )

# ==========================================================
# CODE GENERATOR
# ==========================================================

def generate_code(prefix, model, field_name, organization):
    """
    Generate the next sequential code for a model scoped to an organization.

    Uses transaction.atomic() + select_for_update() to prevent race conditions.
    Skips collisions/gaps by looping until a free candidate is found.
    """
    with transaction.atomic():
        last = (
            model.objects
            .select_for_update()
            .filter(organization=organization)
            .order_by("-id")
            .first()
        )

        if last:
            try:
                number = int(str(getattr(last, field_name)).split("-")[-1]) + 1
            except (ValueError, AttributeError, TypeError):
                number = 1
        else:
            number = 1

        candidate = f"{prefix}-{number:03d}"
        while model.objects.filter(
            **{field_name: candidate, "organization": organization}
        ).exists():
            number += 1
            candidate = f"{prefix}-{number:03d}"

        return candidate

# ==========================================================
# STOCK RESERVATION SERVICES
# ==========================================================

def cleanup_expired_reservations(organization=None, branch=None):
    """Delete all expired reservations."""
    qs = StockReservation.objects.filter(expires_at__lt=timezone.now())
    if organization:
        qs = qs.filter(organization=organization)
    if branch is not None:
        qs = qs.filter(branch=branch)
    count, _ = qs.delete()
    return count

def get_reservation_details(product, organization, branch=None, session_key=None):
    """
    Get complete reservation details in ONE database query.
    Returns dict with all reservation info.
    """
    reservations = StockReservation.objects.filter(
        product=product,
        organization=organization,
        branch=branch,
        expires_at__gte=timezone.now()
    )

    total_reserved  = Decimal('0')
    your_reservation = Decimal('0')
    count = 0

    for res in reservations:
        total_reserved += res.reserved_quantity
        count += 1
        if session_key and res.session_key == session_key:
            your_reservation = res.reserved_quantity

    others_reserved = total_reserved - your_reservation

    return {
        'total_reserved':  float(total_reserved),
        'others_reserved': float(others_reserved),
        'your_reservation': float(your_reservation),
        'count': count,
    }

def get_available_stock(product, organization, branch=None, session_key=None):
    """
    Return stock available for a specific user:
    available = real_stock - reservations_by_OTHERS
    """
    real_stock = get_current_stock(product, organization, branch)

    cleanup_expired_reservations(organization=organization, branch=branch)

    details = get_reservation_details(product, organization, branch, session_key)

    available = max(0, real_stock - details['others_reserved'])
    return float(available)

@transaction.atomic
def set_reservation(session_key, product, organization, branch, quantity, user=None):
    """
    Create or update a reservation for this session+product.
    Accepts optional user to set created_by/updated_by on new reservation.
    """
    cleanup_expired_reservations(organization=organization, branch=branch)

    qty        = Decimal(str(quantity))
    real_stock = Decimal(str(get_current_stock(product, organization, branch)))

    all_reservations = StockReservation.objects.filter(
        product=product,
        organization=organization,
        branch=branch,
        expires_at__gte=timezone.now()
    )

    total_reserved   = Decimal('0')
    current_user_qty = Decimal('0')

    for res in all_reservations:
        total_reserved += res.reserved_quantity
        if res.session_key == session_key:
            current_user_qty = res.reserved_quantity

    others_reserved = total_reserved - current_user_qty
    max_for_user    = max(0, real_stock - others_reserved)

    if qty > max_for_user:
        return {
            'success': False,
            'available_stock': float(max(0, real_stock - others_reserved - current_user_qty)),
            'your_reservation': float(current_user_qty),
            'real_stock': float(real_stock),
            'message': f'Only {float(max_for_user)} units available.',
        }

    expiry = timezone.now() + timedelta(minutes=RESERVATION_TTL_MINUTES)

    defaults = {
        'reserved_quantity': qty,
        'expires_at': expiry,
    }
    # set created_by/updated_by if user provided
    if user:
        defaults['updated_by'] = user
        defaults['created_by'] = user

    StockReservation.objects.update_or_create(
        session_key=session_key,
        product=product,
        organization=organization,
        branch=branch,
        defaults=defaults
    )

    final_details       = get_reservation_details(product, organization, branch, session_key)
    available_for_others = max(0, float(real_stock) - final_details['others_reserved'])

    return {
        'success': True,
        'available_stock': float(available_for_others),
        'your_reservation': float(qty),
        'real_stock': float(real_stock),
        'message': f'Reserved {float(qty)} units.',
    }

def release_reservation(session_key, product, organization, branch):
    """Release (delete) a reservation."""
    StockReservation.objects.filter(
        session_key=session_key,
        product=product,
        organization=organization,
        branch=branch,
    ).delete()

def release_all_session_reservations(session_key, organization, branch=None):
    """Release ALL reservations for a session."""
    StockReservation.objects.filter(
        session_key=session_key,
        organization=organization,
        branch=branch,
    ).delete()

# ==========================================================
# OPENING STOCK SERVICE
# ==========================================================

@transaction.atomic
def create_opening_stock(request, data):
    """Create or update opening stock for a product."""
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)

    product   = Product.objects.get(id=data["product"])
    stock_qty = safe_decimal(data.get("stock"))

    existing = OpeningStock.objects.filter(
        organization=org, branch=branch, product=product
    ).first()

    if existing:
        existing.stock = stock_qty
        existing.updated_by = request.user
        existing.save()
        messages.info(request, f"Updated opening stock for {product.name}.")
        check_low_stock_alert(request, product, int(existing.stock))
    else:
        OpeningStock.objects.create(
            organization=org,
            branch=branch,
            date=safe_date(data.get("date")),
            product_group=product.product_group,
            brand=product.brand,
            category=product.category,
            product=product,
            stock=stock_qty,
            created_by=request.user,
            updated_by=request.user,
        )
        messages.success(request, f"Added opening stock for {product.name}.")

# ==========================================================
# PURCHASE SERVICE
# ==========================================================

@transaction.atomic
def create_purchase(request, data, items):
    """
    Create a purchase transaction with items.
    Returns the created Purchase object.
    """
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    user   = request.user

    code = generate_code("PR", Purchase, "purchase_code", org)

    total = sum(Decimal(i["quantity"]) * Decimal(i["unit_price"]) for i in items)
    paid  = safe_decimal(data.get("paid_amount"))
    due   = total - paid

    purchase = Purchase.objects.create(
        organization=org,
        branch=branch,
        date=safe_date(data.get("date")),
        purchase_code=code,
        supplier_name=data["supplier_name"],
        supplier_mobile=data.get("supplier_mobile"),
        supplier_address=data.get("supplier_address"),
        narration=data.get("narration"),
        total_amount=total,
        paid_amount=paid,
        due_amount=due,
        created_by=user,
        updated_by=user,
    )

    for i in items:
        product = i["product"]
        PurchaseItem.objects.create(
            purchase=purchase,
            organization=org,
            branch=branch,
            category=product.category,
            product_group=i["group"],
            brand=i["brand"],
            product=product,
            quantity=Decimal(i["quantity"]),
            unit_price=Decimal(i["unit_price"]),
            subtotal=Decimal(i["quantity"]) * Decimal(i["unit_price"]),
            created_by=user,
            updated_by=user,
        )

        stock, created = OpeningStock.objects.get_or_create(
            organization=org,
            branch=branch,
            product=product,
            defaults={
                "date": safe_date(data.get("date")),
                "product_group": i["group"],
                "brand": i["brand"],
                "category": product.category,
                "stock": Decimal("0"),
                "created_by": user,
                "updated_by": user,
            },
        )
        stock.stock = Decimal(stock.stock) + Decimal(i["quantity"])
        stock.updated_by = user
        stock.save()

    messages.success(request, f"Purchase {purchase.purchase_code} created successfully.")
    return purchase

# ==========================================================
# SALE SERVICE
# ==========================================================

@transaction.atomic
def create_sale(request, data, items):
    """
    Record a sale transaction with items.
    Pre-validate stock for all items before any DB write.
    Returns the created Sale object.
    """
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    user   = request.user

    # ensure session key exists for reservation-aware checks
    if not request.session.session_key:
        request.session.create()
    session_key = f"u{request.user.id}_{request.session.session_key}"

    # validate ALL stock levels before touching the DB
    for i in items:
        product = i["product"]
        available = Decimal(str(get_available_stock(product, org, branch, session_key)))
        required  = Decimal(i["quantity"])
        if available < required:
            raise ValidationError(
                f"Insufficient stock for '{product.name}': "
                f"{float(available)} available, {float(required)} requested."
            )

    code = generate_code("SL", Sale, "sale_code", org)

    total = sum(Decimal(i["quantity"]) * Decimal(i["unit_price"]) for i in items)
    paid  = safe_decimal(data.get("paid_amount"))
    due   = total - paid

    sale = Sale.objects.create(
        organization=org,
        branch=branch,
        date=safe_date(data.get("date")),
        sale_code=code,
        customer_name=data["customer_name"],
        customer_mobile=data.get("customer_mobile"),
        customer_address=data.get("customer_address"),
        narration=data.get("narration"),
        total_amount=total,
        paid_amount=paid,
        due_amount=due,
        created_by=user,
        updated_by=user,
    )

    for i in items:
        product = i["product"]
        SaleItem.objects.create(
            sale=sale,
            organization=org,
            branch=branch,
            category=product.category,
            product_group=i["group"],
            brand=i["brand"],
            product=product,
            quantity=Decimal(i["quantity"]),
            unit_price=Decimal(i["unit_price"]),
            subtotal=Decimal(i["quantity"]) * Decimal(i["unit_price"]),
            created_by=user,
            updated_by=user,
        )

        # Stock is guaranteed sufficient (checked above) — deduct safely
        stock = OpeningStock.objects.filter(
            organization=org, branch=branch, product=product
        ).first()
        if not stock:
            # Defensive: create stock record if missing (shouldn't happen after validation)
            stock = OpeningStock.objects.create(
                organization=org,
                branch=branch,
                date=safe_date(data.get("date")),
                product_group=product.product_group,
                brand=product.brand,
                category=product.category,
                product=product,
                stock=Decimal("0"),
                created_by=user,
                updated_by=user,
            )
        stock.stock = Decimal(stock.stock) - Decimal(i["quantity"])
        stock.updated_by = user
        stock.save()
        check_low_stock_alert(request, product, int(stock.stock))

    # Release all reservations for this session
    release_all_session_reservations(session_key, org, branch)

    messages.success(request, f"Sale {sale.sale_code} recorded successfully.")
    return sale

# ==========================================================
# PURCHASE RETURN SERVICE
# ==========================================================

@transaction.atomic
def create_purchase_return(request, data, items):
    """
    Record a purchase return.
    Pre-validate that current stock >= return quantity for every item.
    Returns the created PurchaseReturn object.
    """
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    user   = request.user

    # ensure session key exists for reservation-aware checks
    if not request.session.session_key:
        request.session.create()
    session_key = f"u{request.user.id}_{request.session.session_key}"

    # validate ALL items before any write
    for i in items:
        product   = i["product"]
        available = Decimal(str(get_available_stock(product, org, branch, session_key)))
        required  = Decimal(i["quantity"])
        if available < required:
            raise ValidationError(
                f"Cannot return '{product.name}': "
                f"only {float(available)} in stock, {float(required)} requested."
            )

    code = generate_code("PRR", PurchaseReturn, "return_code", org)

    total  = sum(Decimal(i["quantity"]) * Decimal(i["unit_price"]) for i in items)
    refund = safe_decimal(data.get("refund_amount"))
    due    = total - refund

    ret = PurchaseReturn.objects.create(
        organization=org,
        branch=branch,
        date=safe_date(data.get("date")),
        return_code=code,
        total_amount=total,
        refund_amount=refund,
        due_amount=due,
        narration=data.get("narration"),
        supplier_name=data.get("supplier_name", ""),
        supplier_mobile=data.get("supplier_mobile", ""),
        supplier_address=data.get("supplier_address", ""),
        created_by=user,
        updated_by=user,
    )

    for i in items:
        product = i["product"]
        PurchaseReturnItem.objects.create(
            purchase_return=ret,
            organization=org,
            branch=branch,
            product=product,
            brand=product.brand,
            category=product.category,
            product_group=product.product_group,
            quantity=Decimal(i["quantity"]),
            unit_price=Decimal(i["unit_price"]),
            subtotal=Decimal(i["quantity"]) * Decimal(i["unit_price"]),
            created_by=user,
            updated_by=user,
        )

        # Stock is guaranteed sufficient (checked above) — deduct safely
        stock = OpeningStock.objects.filter(
            organization=org, branch=branch, product=product
        ).first()
        if not stock:
            # Defensive: create stock record if missing (shouldn't happen after validation)
            stock = OpeningStock.objects.create(
                organization=org,
                branch=branch,
                date=safe_date(data.get("date")),
                product_group=product.product_group,
                brand=product.brand,
                category=product.category,
                product=product,
                stock=Decimal("0"),
                created_by=user,
                updated_by=user,
            )
        stock.stock = Decimal(stock.stock) - Decimal(i["quantity"])
        stock.updated_by = user
        stock.save()
        check_low_stock_alert(request, product, int(stock.stock))

    # Release session reservations
    release_all_session_reservations(session_key, org, branch)

    messages.success(request, f"Purchase return {ret.return_code} saved.")
    return ret

# ==========================================================
# SALE RETURN SERVICE
# ==========================================================

@transaction.atomic
def create_sale_return(request, data, items):
    """Record a sale return. Returns the created SaleReturn object."""
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    user   = request.user

    code = generate_code("SRR", SaleReturn, "return_code", org)

    total  = sum(Decimal(i["quantity"]) * Decimal(i["unit_price"]) for i in items)
    refund = safe_decimal(data.get("refund_amount"))
    due    = total - refund

    ret = SaleReturn.objects.create(
        organization=org,
        branch=branch,
        date=safe_date(data.get("date")),
        return_code=code,
        total_amount=total,
        refund_amount=refund,
        due_amount=due,
        narration=data.get("narration"),
        customer_name=data.get("customer_name"),
        customer_mobile=data.get("customer_mobile"),
        customer_address=data.get("customer_address"),
        created_by=user,
        updated_by=user,
    )

    for i in items:
        product = i["product"]
        SaleReturnItem.objects.create(
            sale_return=ret,
            organization=org,
            branch=branch,
            category=product.category,
            product_group=product.product_group,
            brand=product.brand,
            product=product,
            quantity=Decimal(i["quantity"]),
            unit_price=Decimal(i["unit_price"]),
            subtotal=Decimal(i["quantity"]) * Decimal(i["unit_price"]),
            created_by=user,
            updated_by=user,
        )

        stock, created = OpeningStock.objects.get_or_create(
            organization=org,
            branch=branch,
            product=product,
            defaults={
                "date": safe_date(data.get("date")),
                "product_group": product.product_group,
                "brand": product.brand,
                "category": product.category,
                "stock": Decimal("0"),
                "created_by": user,
                "updated_by": user,
            },
        )
        stock.stock = Decimal(stock.stock) + Decimal(i["quantity"])
        stock.updated_by = user
        stock.save()

    messages.success(request, f"Sale return {ret.return_code} saved successfully.")
    return ret

# ==========================================================
# REJECT SERVICE
# ==========================================================

@transaction.atomic
def create_reject(request, data):
    """
    Record a supplier-side product reject.

    Validates stock before creating the reject record and deducts stock.
    """
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    user   = request.user

    # Validate product
    product_id = data.get("product")
    if not product_id:
        raise ValidationError("No product selected for rejection.")

    product = Product.objects.filter(id=product_id).first()
    if not product:
        raise ValidationError("Selected product does not exist.")

    # Validate quantity
    qty = safe_decimal(data.get("quantity"))
    if qty <= 0:
        raise ValidationError("Quantity must be greater than zero.")

    # ensure session key exists for reservation-aware checks
    if not request.session.session_key:
        request.session.create()
    session_key = f"u{request.user.id}_{request.session.session_key}"

    # check stock BEFORE creating the reject record using reservation-aware available stock
    available = Decimal(str(get_available_stock(product, org, branch, session_key)))
    if available < qty:
        raise ValidationError(
            f"Cannot reject {float(qty)} of '{product.name}': "
            f"only {float(available)} in stock."
        )

    purchase_id = data.get("purchase")
    purchase    = None
    if purchase_id:
        purchase = Purchase.objects.filter(id=purchase_id).first()

    code = generate_code("RJ", ProductReject, "reject_code", org)

    reject = ProductReject.objects.create(
        organization=org,
        branch=branch,
        date=safe_date(data.get("date")),
        reject_code=code,
        category=product.category,
        product_group=product.product_group,
        brand=product.brand,
        product=product,
        quantity=qty,
        reason=data.get("reason"),
        narration=data.get("narration"),
        purchase=purchase,
        created_by=user,
        updated_by=user,
    )

    # Stock is guaranteed sufficient — deduct safely
    stock = OpeningStock.objects.filter(
        organization=org, branch=branch, product=product
    ).first()
    if not stock:
        # Defensive: create stock record if missing (shouldn't happen after validation)
        stock = OpeningStock.objects.create(
            organization=org,
            branch=branch,
            date=safe_date(data.get("date")),
            product_group=product.product_group,
            brand=product.brand,
            category=product.category,
            product=product,
            stock=Decimal("0"),
            created_by=user,
            updated_by=user,
        )
    stock.stock = Decimal(stock.stock) - qty
    stock.updated_by = user
    stock.save()
    check_low_stock_alert(request, product, int(stock.stock))

    messages.success(
        request,
        f"Reject {code} created successfully: {float(qty)} of {product.name} rejected."
    )

    # Release reservation for this session (if any)
    release_reservation(session_key, product, org, branch)

    return reject
