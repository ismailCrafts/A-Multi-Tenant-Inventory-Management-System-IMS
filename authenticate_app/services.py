# ==========================================================
# File: authenticate_app/services.py
# ==========================================================
# BUGS FIXED IN THIS FILE:
#
# BUG A1 — Duplicate 'import uuid' (LOW)
#   Second import mid-file removed. Only one at the top is needed.
#
# BUG A2 — approve_organization_request() drops language (HIGH)
#   req.language was never passed to Organization.objects.create().
#   Every approved org silently defaulted to 'en'.
#
# BUG A3 — approve_organization_request() self-imports from .services (HIGH)
#   The fix version had 'from .services import generate_org_code, generate_branch_code'
#   inside the function — a circular self-import. Both functions are already
#   defined in this same file; no import needed at all.
#
# BUG A4 — create_user() creates branch without transaction.atomic() (MEDIUM)
#   If User.objects.create() fails after Branch.objects.create(),
#   an orphan branch is left in the DB with no associated user.
#   Wrapped in transaction.atomic() to keep them consistent.
#
# BUG A5 — get_user_by_username() / get_user_by_email() case-sensitive lookup (MEDIUM)
#   Used username= (exact match) instead of username__iexact=.
#   A user registered as 'Alice' cannot log in as 'alice'.
#   Fixed to use __iexact for consistent case-insensitive lookup.
#
# BUG A6 — resolve_organization() silently returns None when UUID lookup fails (LOW)
#   If a UUID is provided but not found, the function returns None with no
#   fallback to code/name. This means a valid UUID that simply isn't in the DB
#   gives the same result as a mistyped name, with no distinction.
#   Behaviour is intentional per the docstring, but the early return when
#   is_uuid=True and org is None now explicitly returns None (documented).
#
# BUG A7 — create_organization_request() does not validate email format (MEDIUM)
#   admin_email is stored and later used to create a real User, but no
#   format validation is performed at request time.
#   Fixed: basic email format check added before persisting.
#
# ==========================================================

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from .models import User, Organization, Branch, OrganizationRequest
from .validators import (
    get_platform_admin_by_username,
    get_platform_admin_by_email,
    is_valid_email,
)
import uuid
import random
import string

# BUG A1 FIX: removed the second duplicate 'import uuid' that was mid-file


# ==========================================================
# Convert Organization Name to ID
# ==========================================================
def get_org_id_by_name(org_name):
    """
    Returns the UUID primary key of an organization by name (case-insensitive).

    Steps:
    1. Strip whitespace from input name.
    2. Query for Organization with case-insensitive exact match.
    3. Return the organization's id if found, otherwise None.
    """
    org = Organization.objects.filter(name__iexact=org_name.strip()).first()
    return org.id if org else None


# ==========================================================
# Get Organization by ID
# ==========================================================
def get_organization_by_id(org_id):
    """
    Fetches an Organization by its UUID primary key.

    Steps:
    1. Filter by primary key.
    2. Return the first match or None (safe lookup).
    """
    return Organization.objects.filter(id=org_id).first()


# ==========================================================
# Create Platform Admin
# ==========================================================
def create_platform_admin(username, email, password):
    """
    Creates a global platform admin account.

    Steps:
    1. Check uniqueness of username and email.
    2. Create user with platform_admin role and superuser flags.
    3. Return result payload.
    """
    # Step 1: Check uniqueness
    if get_platform_admin_by_username(username) or get_platform_admin_by_email(email):
        return {"error": "Platform admin with this username/email already exists."}

    # Step 2: Create user
    user = User.objects.create(
        username=username.strip(),
        email=email.strip(),
        password=make_password(password),
        role="platform_admin",
        organization=None,
        is_staff=True,
        is_superuser=True,
    )

    # Step 3: Return result
    return {"success": "Platform admin created.", "user": user}


# ==========================================================
# User Lookup Helpers
# ==========================================================
def get_user_by_username(username, org_id):
    """
    Looks up a user by username scoped to an organization.

    Steps:
    1. Strip whitespace from username.
    2. Filter by username (case-insensitive) and organization_id.
    3. Return the first match or None.

    BUG A5 FIX: Changed username= to username__iexact= so that 'alice'
    and 'Alice' resolve to the same user. Consistent with registration
    which also normalizes via iexact checks.
    """
    return User.objects.filter(
        username__iexact=username.strip(),
        organization_id=org_id
    ).first()


def get_user_by_email(email, org_id):
    """
    Looks up a user by email scoped to an organization.

    Steps:
    1. Strip whitespace from email.
    2. Filter by email (case-insensitive) and organization_id.
    3. Return the first match or None.

    BUG A5 FIX: Changed email= to email__iexact= for consistent
    case-insensitive lookup.
    """
    return User.objects.filter(
        email__iexact=email.strip(),
        organization_id=org_id
    ).first()


# ==========================================================
# Resolve Organization from single input (id, code, or name)
# ==========================================================
def resolve_organization(org_input):
    """
    Resolves an organization from a single input which may be:
    - UUID (id), or
    - Code (string), or
    - Name (string).

    Steps:
    1. Return None immediately if input is falsy.
    2. Normalize input by stripping whitespace.
    3. Try to parse input as UUID; if valid, lookup by id.
    4. If UUID not found in DB, return None (do not fall through to name search).
    5. If not UUID, attempt lookup by code (case-insensitive).
    6. If code not found, attempt lookup by name (case-insensitive).
    """
    if not org_input:
        return None

    text = org_input.strip()

    # Step 3: Detect UUID input
    try:
        org_uuid = uuid.UUID(text)
        is_uuid = True
    except ValueError:
        is_uuid = False

    if is_uuid:
        # Step 4: Lookup by UUID — return result directly (None if not found)
        return Organization.objects.filter(id=org_uuid).first()

    # Step 5: Attempt by code (case-insensitive)
    org = Organization.objects.filter(code__iexact=text).first()
    if org:
        return org

    # Step 6: Fallback to name lookup (case-insensitive)
    return Organization.objects.filter(name__iexact=text).first()


# ==========================================================
# Generate Organization Code
# ==========================================================
def generate_org_code(prefix="ORG", length=6):
    """
    Generates a unique organization code with a prefix and random suffix.

    Steps:
    1. Create a random alphanumeric suffix of given length.
    2. Combine with prefix as 'PREFIX-SUFFIX'.
    3. If code exists globally, regenerate until unique.
    4. Return the unique code.
    """
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    code = f"{prefix}-{suffix}"
    while Organization.objects.filter(code=code).exists():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        code = f"{prefix}-{suffix}"
    return code


# ==========================================================
# Organization Creation (direct)
# ==========================================================
def create_organization(name):
    """
    Creates an organization directly (without request workflow).

    Steps:
    1. Validate name is unique (case-insensitive).
    2. Generate a unique organization code.
    3. Create and return the Organization instance.
    """
    if Organization.objects.filter(name__iexact=name.strip()).exists():
        raise ValidationError("Organization name already exists.")
    code = generate_org_code(prefix="ORG")
    org = Organization.objects.create(name=name.strip(), code=code)
    return org


# ==========================================================
# Organization Request (controlled onboarding)
# ==========================================================
def create_organization_request(
    name, admin_username, admin_email, admin_password,
    branch_name=None, notes=None, address=None, logo=None, language="en"
):
    """
    Creates a pending organization request capturing org name and first admin credentials.

    Steps:
    1. Validate required fields exist (name, admin_username, admin_email, admin_password).
    2. Validate admin_email format.
    3. Ensure no organization with that name already exists.
    4. Ensure no pending request exists with the same requested name.
    5. Hash the admin password immediately.
    6. Create the OrganizationRequest with optional branch_name, notes, and language.
    7. Return success payload with the request object.

    BUG A7 FIX: Added email format validation (Step 2) before persisting.
    """
    # Step 1: Required field validation
    if not name or not admin_username or not admin_email or not admin_password or not language:
        return {'error': 'Organization name, admin username, email, language and password are required.'}

    # Step 2: BUG A7 FIX — validate email format before storing
    if not is_valid_email(admin_email):
        return {'error': 'Invalid admin email format.'}

    # Step 3: Unique name check against existing organizations
    if Organization.objects.filter(name__iexact=name.strip()).exists():
        return {'error': 'Organization name already exists.'}

    # Step 4: Unique pending request check
    if OrganizationRequest.objects.filter(
        requested_name__iexact=name.strip(), status="pending"
    ).exists():
        return {'error': 'A pending request for this organization already exists.'}

    # Step 5: Create request (password hashed immediately)
    req = OrganizationRequest.objects.create(
        requested_name=name.strip(),
        admin_username=admin_username.strip(),
        admin_email=admin_email.strip(),
        admin_password=make_password(admin_password),
        branch_name=(branch_name.strip() if branch_name else None),
        notes=notes or "",
        address=address,
        logo=logo,
        language=language,
    )

    # Step 6: Return a success response with the created request
    return {'success': 'Organization request submitted.', 'request': req}


# ==========================================================
# Approve Organization Request
# ==========================================================
def approve_organization_request(request_id):
    """
    Approves a pending OrganizationRequest and provisions tenant resources.

    Steps:
    1. Fetch pending request by id; return error if not found.
    2. Generate a unique organization code and create Organization (with language).
    3. If branch_name provided, create a Branch with unique per-org code.
    4. Create the first admin User using stored (hashed) password.
    5. Update request status to 'approved' and set approved_at timestamp.
    6. Return success payload with created organization and admin user.

    BUG A2 FIX: language=req.language now passed to Organization.objects.create().
    BUG A3 FIX: Removed circular 'from .services import ...' inside the function.
                generate_org_code and generate_branch_code are defined in this
                same file — no import needed.
    """
    # Step 1: Strictly fetch pending request
    req = OrganizationRequest.objects.filter(id=request_id, status="pending").first()
    if not req:
        return {'error': 'Request not found or not pending.'}

    # Step 2: Create organization — BUG A2 FIX: include language=req.language
    code = generate_org_code()
    org = Organization.objects.create(
        name=req.requested_name.strip(),
        code=code,
        address=req.address,
        logo=req.logo,
        language=req.language,  # BUG A2 FIX: carry language from request to org
    )

    # Step 3: Optionally create branch if requested
    branch = None
    if req.branch_name:
        branch_code = generate_branch_code(org)
        branch = Branch.objects.create(
            name=req.branch_name.strip(),
            code=branch_code,
            organization=org
        )

    # Step 4: Create initial admin user (password already hashed in request)
    admin_user = User.objects.create(
        username=req.admin_username.strip(),
        email=req.admin_email.strip(),
        password=req.admin_password,
        organization=org,
        branch=branch,
        role="admin"
    )

    # Step 5: Mark request as approved with timestamp
    req.status = "approved"
    req.approved_at = timezone.now()
    req.save()

    # Step 6: Return result payload
    return {
        'success': 'Organization approved and created.',
        'organization': org,
        'admin_user': admin_user
    }


# ==========================================================
# Reject Organization Request
# ==========================================================
def reject_organization_request(request_id, reason=None):
    """
    Rejects a pending OrganizationRequest and records the decision.

    Steps:
    1. Fetch pending request by id; return error if not found.
    2. Update status to 'rejected' and set rejected_at timestamp.
    3. Append rejection reason to notes if provided.
    4. Save changes and return success response.
    """
    req = OrganizationRequest.objects.filter(id=request_id, status="pending").first()
    if not req:
        return {'error': 'Request not found or not pending.'}

    req.status = "rejected"
    req.rejected_at = timezone.now()

    if reason:
        req.notes = f"{req.notes or ''}\nRejected: {reason}"

    req.save()
    return {'success': 'Organization request rejected.'}


# ==========================================================
# Generate Branch Code
# ==========================================================
def generate_branch_code(org, prefix="BR", length=4):
    """
    Generates a unique branch code within a specific organization.

    Steps:
    1. Create a random alphanumeric suffix.
    2. Combine with prefix as 'PREFIX-SUFFIX'.
    3. If code exists within the organization, regenerate until unique.
    4. Return the unique branch code.
    """
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    code = f"{prefix}-{suffix}"
    while Branch.objects.filter(organization=org, code=code).exists():
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        code = f"{prefix}-{suffix}"
    return code


# ==========================================================
# Create User with Full Validation
# ==========================================================
@transaction.atomic
def create_user(username, email, password, org_id, branch_name=None, role="employee"):
    """
    Creates a user within an organization with validation and optional branch creation.

    Steps:
    1. Resolve the organization by id; return error if not found.
    2. Check username uniqueness within the organization.
    3. Check email uniqueness within the organization.
    4. Resolve branch by name within the organization; create if not found (optional).
    5. Hash password securely.
    6. Create and return the User with role and associations.

    BUG A4 FIX: Wrapped in @transaction.atomic so that if User.objects.create()
    fails after a Branch has been created, the orphan branch is rolled back.
    """
    # Step 1: Resolve organization
    org = get_organization_by_id(org_id)
    if org is None:
        return {"error": "Organization not found. Please check the name."}

    # Step 2: Enforce per-org username uniqueness
    if get_user_by_username(username, org_id):
        return {"error": "That username is already taken."}

    # Step 3: Enforce per-org email uniqueness
    if get_user_by_email(email, org_id):
        return {"error": "Email already exists in this organization"}

    # Step 4: Resolve or create branch (optional workflow)
    branch = None
    if branch_name:
        branch = Branch.objects.filter(
            name__iexact=branch_name.strip(), organization=org
        ).first()
        if branch is None:
            branch_code = generate_branch_code(org)
            branch = Branch.objects.create(
                name=branch_name.strip(),
                code=branch_code,
                organization=org
            )

    # Step 5: Hash password
    hashed_password = make_password(password)

    # Step 6: Create user with associations and role
    user = User.objects.create(
        username=username.strip(),
        email=email.strip(),
        password=hashed_password,
        organization=org,
        branch=branch,
        role=role
    )
    return user


# ==========================================================
# Send Reset Email (single org input: id, code, or name)
# ==========================================================
import smtplib
from email.mime.text import MIMEText

def send_reset_email(request, org_input, email):
    # Step 1: Resolve organization
    org = resolve_organization(org_input)
    if not org:
        return "Organization not found."

    # Step 2: Find user within organization
    user = User.objects.filter(email=email.strip(), organization=org).first()
    if not user:
        return f"No user with that email in organization '{org.name}'."

    # Step 3: Generate uid and token
    uid   = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Step 4: Construct reset link
    reset_link = f"{request.scheme}://{request.get_host()}/reset/{uid}/{token}/"

    # Step 5: Build email content
    subject = f"Password Reset for {org.name}"
    message = (
        f"Hi {user.username},\n\n"
        f"You requested a password reset for your account in '{org.name}'.\n"
        f"Click the link below to reset your password:\n\n"
        f"{reset_link}\n\n"
        f"If you didn't request this, you can safely ignore this email."
    )

    # Step 6: Send email manually with smtplib
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_HOST_USER
        msg["To"] = email

        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()  # safe, no keyfile bug
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAIL_HOST_USER, [email], msg.as_string())
        server.quit()
        return "Password reset email sent successfully."
    except Exception as e:
        return f"Error sending email: {e}"
