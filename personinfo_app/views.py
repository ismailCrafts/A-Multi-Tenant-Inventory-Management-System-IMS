from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from stock_app.services import generate_code
from .models import Supplier, Customer
from .services import create_supplier, create_customer
from .validators import validate_person_form
from datetime import date
from authenticate_app.models import User


# ===============================
# PROFILE VIEWS
# ===============================

@login_required
def profile_view(request):
    """
    Render the authenticated user's profile page.

    Steps:
    1. Retrieve the current user from request.
    2. Render the profile template with the user context.
    """
    user = request.user
    return render(request, "personinfo_app/profile.html", {"user": user})


@login_required
def update_profile_view(request):
    """
    Update basic profile fields for the authenticated user.

    Steps:
    1. On POST: validate uniqueness of username/email within the org.
    2. If conflict found: show error and re-render form.
    3. Apply updates, save, and redirect to profile (POST-Redirect-GET).
    4. On GET: render the profile update form populated with current user data.

    Fixes applied:
    - BUG V2: Added per-org uniqueness check for username and email.
    - BUG V3: redirect() after successful POST instead of render().
    """
    if request.method == 'POST':
        user = request.user
        org  = user.organization

        new_username = request.POST.get('username', user.username).strip()
        new_email    = request.POST.get('email', user.email).strip()
        new_phone    = request.POST.get('phone', user.phone)
        new_first    = request.POST.get('first_name', user.first_name)
        new_last     = request.POST.get('last_name', user.last_name)

        # Step 1: Check username uniqueness within same org (exclude self)
        if new_username != user.username:
            if User.objects.filter(username__iexact=new_username, organization=org).exclude(pk=user.pk).exists():
                messages.error(request, "That username is already taken in your organization.")
                return render(request, "personinfo_app/update_profile.html", {"user": user})

        # Step 2: Check email uniqueness within same org (exclude self)
        if new_email != user.email:
            if User.objects.filter(email__iexact=new_email, organization=org).exclude(pk=user.pk).exists():
                messages.error(request, "That email is already used in your organization.")
                return render(request, "personinfo_app/update_profile.html", {"user": user})

        # Step 3: Apply updates and save
        user.username   = new_username
        user.email      = new_email
        user.phone      = new_phone
        user.first_name = new_first
        user.last_name  = new_last
        user.save()

        # Step 4: Redirect (POST-Redirect-GET — prevents double submit on refresh)
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    # GET: show update form
    return render(request, "personinfo_app/update_profile.html", {"user": request.user})


@login_required
def update_profile_image(request):
    """
    Update the authenticated user's profile image.

    Steps:
    1. On POST with a file: assign uploaded file to user's profile_image and save.
    2. Provide success feedback and redirect to profile.
    3. If no file provided: show an error and redirect.
    """
    if request.method == "POST" and request.FILES.get("profile_image"):
        # Step 1: Attach uploaded file to user and persist
        user = request.user
        user.profile_image = request.FILES["profile_image"]
        user.save()
        messages.success(request, "Profile image updated successfully.")
        return redirect("profile")

    # No file uploaded path
    messages.error(request, "No image uploaded.")
    return redirect("profile")


@login_required
def remove_profile_image(request):
    """
    Remove the authenticated user's profile image.

    Steps:
    1. If a profile image exists: delete the file from storage, clear the field, save user.
    2. Provide success message; otherwise inform that no image existed.
    3. Redirect back to profile.
    """
    user = request.user
    if hasattr(user, "profile_image") and user.profile_image:
        # Delete file from storage without saving immediately, then clear field and save
        user.profile_image.delete(save=False)
        user.profile_image = None
        user.save()
        messages.success(request, "Profile image removed successfully.")
    else:
        messages.info(request, "No profile image to remove.")
    return redirect("profile")


# ===============================
# SUPPLIER VIEWS
# ===============================

@login_required
def supplier_list(request):
    """
    List suppliers for the current user's organization and optional branch.

    Steps:
    1. Resolve tenant context (organization and branch) from request.user.
    2. Filter Supplier queryset by organization and branch (if present).
    3. Render supplier list template with the scoped queryset.
    """
    # Step 1: Tenant context
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)

    # Step 2: Build scoped queryset
    qs = Supplier.objects.filter(organization=org)
    if branch:
        qs = qs.filter(branch=branch)

    # Step 3: Render list view
    return render(request, "personinfo_app/supplier_list.html", {"suppliers": qs})


@login_required
def supplier_detail(request, pk):
    """
    Show details for a single supplier and handle deletion.

    Steps:
    1. Resolve tenant context and fetch supplier by pk scoped to organization.
    2. Enforce branch-level access if the user is branch-scoped.
    3. On POST with 'delete': delete supplier and redirect to list with feedback.
    4. On GET: render supplier detail template.
    """
    # Step 1: Tenant context and safe fetch
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    supplier = get_object_or_404(Supplier, pk=pk, organization=org)

    # Step 2: Enforce branch access if applicable
    if branch and supplier.branch and supplier.branch != branch:
        return render(request, "403.html")

    # Step 3: Handle deletion via POST
    if request.method == "POST" and "delete" in request.POST:
        supplier.delete()
        messages.success(request, "Supplier deleted successfully.")
        return redirect("supplier_list")

    # Step 4: Render detail view
    return render(request, "personinfo_app/supplier_detail.html", {"supplier": supplier})


@login_required
def supplier_create(request):
    """
    Create a new supplier.

    Steps:
    - GET:
      1. Pre-generate supplier code and current date.
      2. Render supplier creation form with prefilled values.
    - POST:
      1. Validate form using validate_person_form.
      2. On validation failure: re-render form with error, re-using the
         submitted code instead of generating a new one (BUG V5 fix).
      3. On success: delegate creation to create_supplier service, show success,
         redirect to detail.

    Fixes applied:
    - BUG V5: On validation failure, re-use submitted code from POST data
      instead of calling generate_code() again (avoids showing a different code).
    """
    if request.method == "POST":
        # Step 1: Validate inputs
        valid, err = validate_person_form(request.POST)
        if not valid:
            messages.error(request, err)
            # Step 2: Re-use the code already shown in the form (BUG V5 fix)
            submitted_code = request.POST.get('code') or generate_code('SUP', Supplier, 'code', request.user.organization)
            today = date.today().isoformat()
            return render(request, "personinfo_app/supplier_form.html", {
                "next_code":  submitted_code,
                "today":      today,
                "form_data":  request.POST,
            })

        # Step 3: Create supplier via service layer (service sets created_by/updated_by)
        supplier = create_supplier(request, request.POST)
        messages.success(request, f"Supplier created: {supplier.code} - {supplier.name}")
        return redirect("supplier_detail", pk=supplier.pk)

    # GET: pre-generate code and date, then render form
    next_code = generate_code('SUP', Supplier, 'code', request.user.organization)
    today = date.today().isoformat()
    return render(request, "personinfo_app/supplier_form.html", {"next_code": next_code, "today": today})


@login_required
def supplier_update(request, pk):
    """
    Update an existing supplier.

    Steps:
    1. Resolve tenant context and fetch supplier by pk scoped to organization.
    2. Enforce branch-level access if applicable.
    3. On POST: validate inputs.
    4. Apply updates to supplier fields, set updated_by, and save.
    5. Provide feedback and redirect to detail.
    6. On GET: render prefilled supplier form.

    Fixes applied:
    - BUG V6: Corrected duplicate "Step 3" labels — now Steps 3, 4, 5 are distinct.
    """
    # Step 1: Tenant context and fetch
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    supplier = get_object_or_404(Supplier, pk=pk, organization=org)

    # Step 2: Enforce branch access
    if branch and supplier.branch and supplier.branch != branch:
        return render(request, "403.html")

    if request.method == "POST":
        # Step 3: Validate inputs
        valid, err = validate_person_form(request.POST)
        if not valid:
            messages.error(request, err)
            return render(request, "personinfo_app/supplier_form.html", {"supplier": supplier})

        # Step 4: Apply updates and persist
        supplier.name    = request.POST.get("name")
        supplier.mobile  = request.POST.get("mobile")
        supplier.address = request.POST.get("address")
        supplier.email   = request.POST.get("email")
        supplier.updated_by = request.user   # NEW: track updater
        supplier.save()

        # Step 5: Feedback and redirect
        messages.success(request, f"Supplier updated: {supplier.code} - {supplier.name}")
        return redirect("supplier_detail", pk=supplier.pk)

    # Step 6: Render prefilled form on GET
    return render(request, "personinfo_app/supplier_form.html", {"supplier": supplier})


@login_required
def supplier_lookup(request):
    """
    Tenant-scoped lookup endpoint for suppliers by mobile or code.

    Steps:
    1. Read 'identifier' from GET params; return 400 if missing.
    2. Scope query to the current user's organization.
    3. Try to find Supplier by mobile within org; if not found, try by code.
    4. If found, return JSON payload with supplier details; otherwise return 404.

    Fixes applied:
    - BUG V1: Removed from authenticate_app.services import * (was unused/dangerous).
    - BUG V4: Added @login_required — was publicly accessible before.
    - BUG V4: All queries now scoped to request.user.organization (tenant isolation).
    - BUG V4: Uses filter().first() instead of get() to avoid MultipleObjectsReturned.
    """
    # Step 1: Read identifier
    identifier = request.GET.get("identifier")
    if not identifier:
        return JsonResponse({"error": "No identifier provided"}, status=400)

    # Step 2: Scope to current user's organization
    org = request.user.organization

    # Step 3: Lookup by mobile within org, then by code within org
    supplier = (
        Supplier.objects.filter(mobile=identifier, organization=org).first()
        or Supplier.objects.filter(code=identifier, organization=org).first()
    )

    # Step 4: Return result or 404
    if not supplier:
        return JsonResponse({"error": "Supplier not found"}, status=404)

    return JsonResponse({
        "name":    supplier.name,
        "mobile":  supplier.mobile,
        "address": supplier.address,
        "email":   supplier.email,
    })


# ===============================
# CUSTOMER VIEWS
# ===============================

@login_required
def customer_list(request):
    """
    List customers for the current user's organization and optional branch.

    Steps:
    1. Resolve tenant context.
    2. Filter Customer queryset by organization and branch (if present).
    3. Render customer list template with the scoped queryset.
    """
    # Step 1: Tenant context
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)

    # Step 2: Build scoped queryset
    qs = Customer.objects.filter(organization=org)
    if branch:
        qs = qs.filter(branch=branch)

    # Step 3: Render list view
    return render(request, "personinfo_app/customer_list.html", {"customers": qs})


@login_required
def customer_detail(request, pk):
    """
    Show details for a single customer and handle deletion.

    Steps:
    1. Resolve tenant context and fetch customer by pk scoped to organization.
    2. Enforce branch-level access if the user is branch-scoped.
    3. On POST with 'delete': delete customer and redirect to list with feedback.
    4. On GET: render customer detail template.
    """
    # Step 1: Tenant context and safe fetch
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    customer = get_object_or_404(Customer, pk=pk, organization=org)

    # Step 2: Enforce branch access if applicable
    if branch and customer.branch and customer.branch != branch:
        return render(request, "403.html")

    # Step 3: Handle deletion via POST
    if request.method == "POST" and "delete" in request.POST:
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect("customer_list")

    # Step 4: Render detail view
    return render(request, "personinfo_app/customer_detail.html", {"customer": customer})


@login_required
def customer_create(request):
    """
    Create a new customer.

    Steps:
    - GET:
      1. Pre-generate customer code and current date.
      2. Render customer creation form with prefilled values.
    - POST:
      1. Validate form using validate_person_form.
      2. On validation failure: re-render form with error, re-using the
         submitted code instead of generating a new one (BUG V5 fix).
      3. On success: delegate creation to create_customer service, show success,
         redirect to detail.

    Fixes applied:
    - BUG V5: On validation failure, re-use submitted code from POST data
      instead of calling generate_code() again.
    """
    if request.method == "POST":
        # Step 1: Validate inputs
        valid, err = validate_person_form(request.POST)
        if not valid:
            messages.error(request, err)
            # Step 2: Re-use the code already shown in the form (BUG V5 fix)
            submitted_code = request.POST.get('code') or generate_code('CUS', Customer, 'code', request.user.organization)
            today = date.today().isoformat()
            return render(request, "personinfo_app/customer_form.html", {
                "next_code":  submitted_code,
                "today":      today,
                "form_data":  request.POST,
            })

        # Step 3: Create customer via service layer (service sets created_by/updated_by)
        customer = create_customer(request, request.POST)
        messages.success(request, f"Customer created: {customer.code} - {customer.name}")
        return redirect("customer_detail", pk=customer.pk)

    # GET: pre-generate code and date, then render form
    next_code = generate_code('CUS', Customer, 'code', request.user.organization)
    today = date.today().isoformat()
    return render(request, "personinfo_app/customer_form.html", {"next_code": next_code, "today": today})


@login_required
def customer_update(request, pk):
    """
    Update an existing customer.

    Steps:
    1. Resolve tenant context and fetch customer by pk scoped to organization.
    2. Enforce branch-level access if applicable.
    3. On POST: validate inputs.
    4. Apply updates to customer fields, set updated_by, and save.
    5. Provide feedback and redirect to detail.
    6. On GET: render prefilled customer form.

    Fixes applied:
    - BUG V6: Corrected duplicate "Step 3" labels — now Steps 3, 4, 5 are distinct.
    """
    # Step 1: Tenant context and fetch
    org    = request.user.organization
    branch = getattr(request.user, "branch", None)
    customer = get_object_or_404(Customer, pk=pk, organization=org)

    # Step 2: Enforce branch access
    if branch and customer.branch and customer.branch != branch:
        return render(request, "403.html")

    if request.method == "POST":
        # Step 3: Validate inputs
        valid, err = validate_person_form(request.POST)
        if not valid:
            messages.error(request, err)
            return render(request, "personinfo_app/customer_form.html", {"customer": customer})

        # Step 4: Apply updates and persist
        customer.name    = request.POST.get("name")
        customer.mobile  = request.POST.get("mobile")
        customer.address = request.POST.get("address")
        customer.email   = request.POST.get("email")
        customer.updated_by = request.user   # NEW: track updater
        customer.save()

        # Step 5: Feedback and redirect
        messages.success(request, f"Customer updated: {customer.code} - {customer.name}")
        return redirect("customer_detail", pk=customer.pk)

    # Step 6: Render prefilled form on GET
    return render(request, "personinfo_app/customer_form.html", {"customer": customer})


@login_required
def customer_lookup(request):
    """
    Tenant-scoped lookup endpoint for customers by mobile or code.

    Steps:
    1. Read 'identifier' from GET params; return 400 if missing.
    2. Scope query to the current user's organization.
    3. Try to find Customer by mobile within org; if not found, try by code.
    4. If found, return JSON payload with customer details; otherwise return 404.

    Fixes applied:
    - BUG V4: Added @login_required — was publicly accessible before.
    - BUG V4: All queries now scoped to request.user.organization (tenant isolation).
    - BUG V4: Uses filter().first() instead of get() to avoid MultipleObjectsReturned.
    """
    # Step 1: Read identifier
    identifier = request.GET.get("identifier")
    if not identifier:
        return JsonResponse({"error": "No identifier provided"}, status=400)

    # Step 2: Scope to current user's organization
    org = request.user.organization

    # Step 3: Lookup by mobile within org, then by code within org
    customer = (
        Customer.objects.filter(mobile=identifier, organization=org).first()
        or Customer.objects.filter(code=identifier, organization=org).first()
    )

    # Step 4: Return result or 404
    if not customer:
        return JsonResponse({"error": "Customer not found"}, status=404)

    return JsonResponse({
        "name":    customer.name,
        "mobile":  customer.mobile,
        "address": customer.address,
        "email":   customer.email,
    })
