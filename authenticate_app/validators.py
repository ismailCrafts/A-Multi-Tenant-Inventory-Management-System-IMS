# ==========================================================
# File: app/validators.py
# ==========================================================
from .models import User, Organization


# ==========================================================
# Section: Get Organization by ID
# ==========================================================
def get_organization_by_id(org_id):
    """
    Looks for an organization with the given ID.
    Steps:
    1. Query Organization by ID.
    2. Return the first match if found.
    3. Return None if not found.
    """
    org = Organization.objects.filter(id=org_id).first()
    return org


from .models import User

# ==========================================================
# Section: Get Platform Admin by Username
# ==========================================================
def get_platform_admin_by_username(username):
    """
    Looks up a global platform admin by username.
    """
    return User.objects.filter(
        username__iexact=username.strip(),
        role="platform_admin",
        organization__isnull=True
    ).first()

# ==========================================================
# Section: Get Platform Admin by Email
# ==========================================================
def get_platform_admin_by_email(email):
    """
    Looks up a global platform admin by email.
    """
    return User.objects.filter(
        email__iexact=email.strip(),
        role="platform_admin",
        organization__isnull=True
    ).first()


# ==========================================================
# Section: Check if Username Exists in Organization
# ==========================================================
def get_user_by_username(username, org_id):
    """
    Checks if a user with a specific username exists in an organization.
    Steps:
    1. Resolve organization by ID.
    2. If org exists, query User by username + org (case-insensitive).
    3. Return User object if found, else None.
    4. If org does not exist, return None.
    """
    org = get_organization_by_id(org_id)
    if org is not None:
        user = User.objects.filter(username__iexact=username.strip(), organization=org).first()
        return user if user is not None else None
    return None


# ==========================================================
# Section: Check if Email Exists in Organization
# ==========================================================
def get_user_by_email(email, org_id):
    """
    Checks if a user with a specific email exists in an organization.
    Steps:
    1. Resolve organization by ID.
    2. If org exists, query User by email + org (case-insensitive).
    3. Return User object if found, else None.
    4. If org does not exist, return None.
    """
    org = get_organization_by_id(org_id)
    if org is not None:
        user = User.objects.filter(email__iexact=email.strip(), organization=org).first()
        return user if user is not None else None
    return None


# ==========================================================
# Section: Simple Email Validator
# ==========================================================
def is_valid_email(email):
    """
    Validates basic email format.
    Steps:
    1. Ensure email string exists.
    2. Check for '@' and '.' characters.
    3. Return True if valid, else False.
    """
    if not email:
        return False
    if '@' in email and '.' in email:
        return True
    return False


# ==========================================================
# Section: Simple Password Strength Validator
# ==========================================================
def is_strong_password(password):
    """
    Validates password strength.
    Requirements:
    - At least 8 characters
    - Contains uppercase, lowercase, digit, and special character
    Steps:
    1. Check length >= 8.
    2. Iterate characters to flag conditions.
    3. Return True if all conditions met, else False.
    """
    if not password or len(password) < 8:
        return False

    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False

    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif not char.isalnum():
            has_special = True

    return has_upper and has_lower and has_digit and has_special
