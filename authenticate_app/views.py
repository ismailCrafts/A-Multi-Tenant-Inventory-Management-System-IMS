from django.utils import translation 
from django.conf import settings
from django.utils.translation import LANGUAGE_SESSION_KEY
# ==========================================================
# File: authenticate_app/views.py
# ==========================================================
from django.shortcuts import render, redirect
from django.contrib import messages
from .services import *
from .models import *
from .validators import *
from django.contrib.auth import login, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from .utils import get_client_ip
from django.contrib.auth import authenticate, login

from django.utils import translation

# ==========================================================
# Platform Admin Login
# ==========================================================
def platform_admin_login(request):
    """
    Handles login for global platform admins.
    """
    if request.method == "POST":
        # Step 1: Read credentials
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Step 2: Lookup platform admin
        user = get_platform_admin_by_username(username)
        if not user:
            messages.error(request, "Platform admin not found.")
            return redirect("platform_admin_login")

        # Step 3: Validate password
        if check_password(password, user.password):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            messages.success(request, f"Welcome back, Platform Admin {username}!")
            return redirect("profile")
        else:
            messages.error(request, "Incorrect password.")
            return redirect("platform_admin_login")

    # Step 4: Render login form
    return render(request, "auth/platform_admin_login.html")


# ===============================
# Organization Request
# ===============================
def create_organization(request):
    """
    Handles the organization onboarding request form.

    Behavior:
    - On POST: Validates required fields and creates a pending OrganizationRequest.
    - On GET: Renders the request form template.

    Flow:
    1. Read form fields from POST.
    2. Delegate creation to services layer (create_organization_request).
    3. Show appropriate feedback via messages and redirect.
    4. Render form on GET.
    """
    if request.method == "POST":
        # Step 1: Collect inputs from the form
        org_address = request.POST.get("address") 
        org_logo = request.FILES.get("logo")
        org_name = request.POST.get("org_name")
        org_lang = request.POST.get('language')
        admin_username = request.POST.get("admin_username")
        admin_email = request.POST.get("admin_email")
        admin_password = request.POST.get("admin_password")
        branch_name = request.POST.get("branch_name")
        notes = request.POST.get("notes")

       # Step 2: Create a pending organization request via service
        result = create_organization_request(
            name=org_name,
            admin_username=admin_username,
            admin_email=admin_email,
            admin_password=admin_password,
            branch_name=branch_name,
            notes=notes,
            address=org_address,
            logo=org_logo,
            language=org_lang,
        )

        # Step 3: Handle error/success with messages and redirect
        if "error" in result:
            messages.error(request, result["error"])
            return redirect("create_organization")

        messages.info(request, "Organization request submitted. Awaiting approval.")
        return redirect("login")

    # Step 4: Render form for GET requests
    return render(request, "auth/create_organization.html")


# ===============================
# User Registration
# ===============================
def user_registration(request):
    """
    Handles user self-registration into a specific organization.

    Behavior:
    - On POST: Validates input, creates user via service, then redirects with feedback.
    - On GET: Displays the registration form with available organizations.

    Flow:
    1. Read inputs from POST and resolve organization id by name.
    2. Call create_user service for validation and creation.
    3. Display error/success messages and redirect accordingly.
    4. Render form on GET with organization list.
    """
    if request.method == 'POST':
        # Step 1: Collect inputs from the form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        org_name = request.POST.get('organization')
        branch_name = request.POST.get('branch')
        role = request.POST.get('role', 'employee')

        # Step 2: Resolve org_id from org_name (case-insensitive)
        org_id = get_org_id_by_name(org_name)

        # Step 3: Create user with validation via service
        result = create_user(username, email, password, org_id, branch_name, role)

        # Step 4: Handle error/success paths
        if isinstance(result, dict) and 'error' in result:
            messages.error(request, result['error'])
            return redirect('user_registration')
        else:
            messages.success(request, f"Welcome, {username}! Your account has been created.")
            return redirect('login')

    # Step 5: Render registration form with organizations list
    orgs = Organization.objects.all()
    return render(request, 'auth/user_registration.html', {'organizations': orgs})


# ===============================
# User Login
# ===============================
# def user_login(request):
#     """
#     Handles user login with tenant scoping and audit logging.

#     Behavior:
#     - On POST: Validates org input, username, and password. Logs in user and records LoginHistory.
#     - On GET: Renders login form and shows message if 'next' is present.

#     Flow:
#     1. Resolve organization from org_input (UUID/code/name).
#     2. Lookup user within that organization.
#     3. Validate account status and password.
#     4. Log login event (IP, org, branch) and authenticate session.
#     5. Redirect to 'next' or profile with feedback.
#     6. Render form on GET with organizations list.
#     """
#     if request.method == 'POST':
#         # Step 1: Read credentials and organization input
#         username = request.POST.get('username')
#         password = request.POST.get('password')
#         org_input = request.POST.get('organization')

#         # Step 2: Resolve organization from input (id/code/name)
#         org = resolve_organization(org_input)
#         if not org:
#             messages.error(request, "Organization not found.")
#             return redirect('login')

#         # Step 3: Fetch user within the resolved organization
#         user = get_user_by_username(username, org.id)
#         if user is None:
#             messages.error(request, "Invalid username for this organization.")
#             return redirect('login')

#         # Step 4: Check account activation status
#         if not user.is_active:
#             messages.error(request, "Your account is not active yet.")
#             return redirect('login')

#         # Step 5: Validate password and perform login
#         if check_password(password, user.password):
#             # Explicitly set backend before login() when authenticating manually
#             user.backend = 'django.contrib.auth.backends.ModelBackend'

#             # Step 6: Record login history with IP and tenant context
#             ip_address = get_client_ip(request)
#             LoginHistory.objects.create(
#                 user=user,
#                 organization=user.organization,
#                 branch=user.branch,
#                 ip_address=ip_address
#             )

#             # Step 7: Start session and redirect with success
#             login(request, user)
#             # Apply organization language 
#             if user.organization and user.organization.language: 
#                 lang = user.organization.language 
#                 # activate the language
#                 translation.activate(lang)
#                 request.session['django_language'] = lang
#             messages.success(request, f"Welcome back, {username}!")
#             next_url = request.POST.get('next') or request.GET.get('next')
#             return redirect(next_url or 'profile')
#         else:
#             # Step 8: Password mismatch path
#             messages.error(request, "Incorrect password.")
#             return redirect('login')

#     # Step 9: Inform about required login if redirected with ?next=
#     if 'next' in request.GET:
#         messages.info(request, "Please log in to continue.")

#     # Step 10: Render login form with list of organizations
#     orgs = Organization.objects.all()
#     return render(request, 'auth/login.html', {'organizations': orgs})


def user_login(request):
    if request.method == 'POST':
        # Step 1: Read username (not email) + password + org from form
        username = request.POST.get('username')
        password = request.POST.get('password')
        org_input = request.POST.get('organization')

        # Step 2: Resolve org from name/code/UUID — defined in services.py
        org = resolve_organization(org_input)
        if not org:
            messages.error(request, "Organization not found.")
            return redirect('login')

        # Step 3: Django calls TenantUsernameBackend.authenticate()
        # which does: User.objects.get(username__iexact=username, organization=org)
        user = authenticate(
            request,
            username=username,
            password=password,
            organization=org   # ← passed to backend so it can scope lookup
        )

        if user:  # ← fixed indentation here
            login(request, user)

            # Determine org language
            lang = (
                user.organization.language
                if user.organization and user.organization.language
                else 'en'
            )
            translation.activate(lang)

            # Build response and set cookie
            response = redirect('profile')
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)

            messages.success(request, f"Welcome back, {user.username}!")
            return response

        else:
            messages.error(request, "Invalid credentials.")
            return redirect('login')

    return render(request, 'auth/login.html')





# ===============================
# User Logout
# ===============================
@login_required
def user_logout(request):
    """
    Logs out the authenticated user and provides feedback.

    Flow:
    1. Call Django's logout to end the session.
    2. Show success message.
    3. Redirect to login page.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


# ===============================
# Change Password
# ===============================
@login_required
def change_password(request):
    """
    Allows an authenticated user to change their password.

    Behavior:
    - On POST: Validates current password and new password confirmation, then updates password.
    - On GET: Renders the profile page (containing the change password form).

    Flow:
    1. Read current/new/confirm passwords from POST.
    2. Validate current password correctness.
    3. Ensure new password matches confirmation.
    4. Hash new password and save.
    5. Provide feedback and redirect to login.
    """
    if request.method == 'POST':
        # Step 1: Read password inputs
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Step 2: Get the authenticated user
        user = request.user

        # Step 3: Validate current password
        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return render(request, 'personinfo_app/profile.html')

        # Step 4: Confirm new password entries match
        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return render(request, 'personinfo_app/profile.html')

        # Optional strength check (kept commented as per existing behavior)
        # if not is_strong_password(new_password):
        #     messages.error(request, "Password must be strong with every combination.")
        #     return redirect('change_password')

        # Step 5: Hash and save new password
        user.password = make_password(new_password)
        user.save()

        # Step 6: Feedback and redirect
        messages.success(request, "Your password has been updated successfully.")
        return redirect('login')

    # Step 7: Render profile page containing the change password form on GET
    return render(request, 'personinfo_app/profile.html')


# ===============================
# Password Reset Request
# ===============================
def password_reset_request(request):
    """
    Initiates a password reset process for a user within a tenant.

    Behavior:
    - On POST: Validates organization input and email format, then attempts to send reset email.
    - On GET: Renders the password reset request form.

    Flow:
    1. Read organization input and email.
    2. Validate both are present and email format is correct.
    3. Delegate email sending to service (send_reset_email).
    4. Provide feedback via messages and redirect.
    5. Render form on GET.
    """
    if request.method == "POST":
        # Step 1: Collect inputs
        org_input = request.POST.get("organization")
        email = request.POST.get("email")

        # Step 2: Validate required fields
        if not org_input or not email:
            messages.error(request, "Organization and email are required.")
            return redirect('password_reset')

        # Step 3: Validate email format using validators
        if not is_valid_email(email):
            messages.error(request, "Invalid email format.")
            return redirect('password_reset')

        # Step 4: Send reset email via service and surface message
        msg = send_reset_email(request, org_input, email)
        messages.info(request, msg)
        return redirect('password_reset')

    # Step 5: Render reset request form
    return render(request, "auth/reset_password.html")


# ===============================
# Password Reset Confirm
# ===============================
def password_reset_confirm(request, uidb64, token):
    """
    Confirms a password reset for a user using uid and token.

    Flow:
    1. Decode uidb64 and fetch user.
    2. Validate reset token for the fetched user.
    3. On POST: Validate new password inputs and update user password.
    4. Provide success/error feedback and redirect appropriately.
    5. Render confirmation form on GET.
    """
    # Step 1: Decode user id from base64 and fetch user
    uid = urlsafe_base64_decode(uidb64).decode()
    user = User.objects.filter(pk=uid).first()
    if not user:
        messages.error(request, "Invalid link.")
        return redirect('password_reset')

    # Step 2: Validate token for the user
    if not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired reset link.")
        return redirect('password_reset')

    if request.method == "POST":
        # Step 3: Read new password inputs
        password = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")

        # Step 4: Validate both fields provided
        if not password or not confirm:
            messages.error(request, "Both password fields are required.")
            return redirect(request.path)

        # Step 5: Ensure new password matches confirmation
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        # __________________________________
        # Password strength checks (optional)
        # __________________________________
        # if not is_strong_password(password):
        #     messages.error(request, "Password must be strong with every combination.")
        #     return redirect(request.path)

        # Step 6: Hash new password and save
        user.password = make_password(password)
        user.save()

        # Step 7: Feedback and redirect to login
        messages.success(request, "Password reset successful!")
        return redirect('login')

    # Step 8: Render reset confirmation template on GET
    return render(request, "auth/reset_password_confirm.html", {"uid": uidb64, "token": token})




@login_required
def update_org_logo(request):
    if request.method == "POST" and request.FILES.get("logo"):
        org = request.user.organization
        org.logo = request.FILES["logo"]
        org.save()
        messages.success(request, "Organization logo updated successfully.")
    return redirect("profile")


from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

@login_required
def remove_org_logo(request):
    if request.method == "POST":
        org = request.user.organization
        if org.logo:
            org.logo.delete(save=False)  
            org.logo = None              
            org.save()
            messages.success(request, "Organization logo removed successfully.")
            return JsonResponse({"status": "ok"})
        return JsonResponse({"status": "no_logo"})
    return JsonResponse({"status": "invalid"}, status=400)
