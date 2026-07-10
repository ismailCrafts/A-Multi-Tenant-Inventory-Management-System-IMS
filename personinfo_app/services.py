from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from .models import Supplier, Customer
from stock_app.services import generate_code


# ==========================================================
# GET SUPPLIER SERVICE
# ==========================================================
def get_supplier(identifier, org, branch=None):
    """
    Retrieves a supplier by code or mobile within an organization/branch.

    Steps:
    1. Build base queryset scoped to organization.
    2. If branch provided, filter by branch.
    3. Lookup by code; if found return immediately.
    4. Lookup by mobile; if found return immediately.
    5. Return None if not found.

    Fixes applied:
    - BUG S1: Replaced double-query pattern (exists() + get()) with a single
      filter().first() call per lookup. The old pattern ran TWO DB queries
      for every check — one for exists() and one for get() — which is wasteful
      and introduces a race condition (record could be deleted between the two).
    """
    # Step 1: Base queryset scoped to organization
    qs = Supplier.objects.filter(organization=org)

    # Step 2: Narrow to branch if provided
    if branch:
        qs = qs.filter(branch=branch)

    # Step 3: Lookup by code (single query)
    supplier = qs.filter(code=identifier).first()
    if supplier:
        return supplier

    # Step 4: Lookup by mobile (single query)
    supplier = qs.filter(mobile=identifier).first()
    if supplier:
        return supplier

    # Step 5: Not found
    return None


# ==========================================================
# GET CUSTOMER SERVICE
# ==========================================================
def get_customer(identifier, org, branch=None):
    """
    Retrieves a customer by code or mobile within an organization/branch.

    Steps:
    1. Build base queryset scoped to organization.
    2. If branch provided, filter by branch.
    3. Lookup by code; if found return immediately.
    4. Lookup by mobile; if found return immediately.
    5. Return None if not found.

    Fixes applied:
    - BUG S1: Same double-query fix as get_supplier above.
    """
    # Step 1: Base queryset scoped to organization
    qs = Customer.objects.filter(organization=org)

    # Step 2: Narrow to branch if provided
    if branch:
        qs = qs.filter(branch=branch)

    # Step 3: Lookup by code (single query)
    customer = qs.filter(code=identifier).first()
    if customer:
        return customer

    # Step 4: Lookup by mobile (single query)
    customer = qs.filter(mobile=identifier).first()
    if customer:
        return customer

    # Step 5: Not found
    return None


# ==========================================================
# CREATE SUPPLIER SERVICE
# ==========================================================
def create_supplier(request, data):
    """
    Creates a new supplier tied to the current user's org/branch.

    Steps:
    1. Resolve organization and branch from request.user.
    2. Validate required fields (name, mobile) are present.
    3. Check mobile is not already used within this organization.
    4. Generate next supplier code scoped to this organization.
    5. Create Supplier inside an atomic transaction with IntegrityError guard.
    6. Return created supplier.

    Fixes applied:
    - BUG S2: Added validation for required fields before hitting the DB.
    - BUG S3: Added per-org duplicate mobile check — prevents IntegrityError
      crash when the same mobile is submitted twice within the same org.
    - BUG S4: Wrapped Supplier.objects.create() in transaction.atomic() with
      IntegrityError catch — handles race conditions gracefully instead of
      crashing with a 500 error.
    - NEW: Track created_by and updated_by from request.user.
    """
    # Step 1: Resolve org/branch from the logged-in user
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Validate required fields
    name   = (data.get('name') or '').strip()
    mobile = (data.get('mobile') or '').strip()

    if not name:
        raise ValidationError("Supplier name is required.")
    if not mobile:
        raise ValidationError("Supplier mobile is required.")

    # Step 3: Check mobile uniqueness within this organization
    if Supplier.objects.filter(mobile=mobile, organization=org).exists():
        raise ValidationError(
            f"A supplier with mobile '{mobile}' already exists in your organization."
        )

    # Step 4: Generate next code scoped to this org
    next_code = generate_code('SUP', Supplier, 'code', org)

    # Step 5: Create supplier with IntegrityError protection
    try:
        with transaction.atomic():
            supplier = Supplier.objects.create(
                code=next_code,
                name=name,
                mobile=mobile,
                address=data.get('address'),
                email=data.get('email'),
                organization=org,
                branch=branch,
                created_by=request.user,
                updated_by=request.user
            )
    except IntegrityError:
        raise ValidationError(
            "Could not create supplier due to a duplicate code or mobile. Please try again."
        )

    # Step 6: Return the created supplier
    return supplier


# ==========================================================
# CREATE CUSTOMER SERVICE
# ==========================================================
def create_customer(request, data):
    """
    Creates a new customer tied to the current user's org/branch.

    Steps:
    1. Resolve organization and branch from request.user.
    2. Validate required fields (name, mobile) are present.
    3. Check mobile is not already used within this organization.
    4. Generate next customer code scoped to this organization.
    5. Create Customer inside an atomic transaction with IntegrityError guard.
    6. Return created customer.

    Fixes applied:
    - BUG S2: Added validation for required fields before hitting the DB.
    - BUG S3: Added per-org duplicate mobile check — prevents IntegrityError
      crash when the same mobile is submitted twice within the same org.
    - BUG S4: Wrapped Customer.objects.create() in transaction.atomic() with
      IntegrityError catch — handles race conditions gracefully.
    - NEW: Track created_by and updated_by from request.user.
    """
    # Step 1: Resolve org/branch from the logged-in user
    org    = request.user.organization
    branch = getattr(request.user, 'branch', None)

    # Step 2: Validate required fields
    name   = (data.get('name') or '').strip()
    mobile = (data.get('mobile') or '').strip()

    if not name:
        raise ValidationError("Customer name is required.")
    if not mobile:
        raise ValidationError("Customer mobile is required.")

    # Step 3: Check mobile uniqueness within this organization
    if Customer.objects.filter(mobile=mobile, organization=org).exists():
        raise ValidationError(
            f"A customer with mobile '{mobile}' already exists in your organization."
        )

    # Step 4: Generate next code scoped to this org
    next_code = generate_code('CUS', Customer, 'code', org)

    # Step 5: Create customer with IntegrityError protection
    try:
        with transaction.atomic():
            customer = Customer.objects.create(
                code=next_code,
                name=name,
                mobile=mobile,
                address=data.get('address'),
                email=data.get('email'),
                organization=org,
                branch=branch,
                created_by=request.user,
                updated_by=request.user
            )
    except IntegrityError:
        raise ValidationError(
            "Could not create customer due to a duplicate code or mobile. Please try again."
        )

    # Step 6: Return the created customer
    return customer
