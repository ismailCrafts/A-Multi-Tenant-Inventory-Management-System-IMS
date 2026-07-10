from django.urls import path
from . import views

# ==========================================================
# AUTH URLS
# ==========================================================
urlpatterns = [
    # Step 0: Organization request (controlled onboarding)
    path('organization/create/', views.create_organization, name='create_organization'),

    # Step 1: User registration (signup)
    path('signup/', views.user_registration, name='user_registration'),

    # Step 2: User login
    path('login/', views.user_login, name='login'),

    # Step 3: User logout
    path('logout/', views.user_logout, name='logout'),

    # Step 4: Change password (for logged-in users)
    path('change_password/', views.change_password, name='change_password'),

    # Step 5: Request password reset (forgot password)
    path('reset-password/', views.password_reset_request, name='password_reset'),

    # Step 6: Confirm password reset (via email link)
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    
    path("platform-admin-login/", views.platform_admin_login, name="platform_admin_login"), 

    path("update-org-logo/", views.update_org_logo, name="update_org_logo"),

    path("remove-org-logo/", views.remove_org_logo, name="remove_org_logo"),


]
