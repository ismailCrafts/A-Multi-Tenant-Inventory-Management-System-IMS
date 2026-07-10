# dashboard_app/admin.py
from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect
from .views import error_lookup

class ErrorLookupAdmin(admin.ModelAdmin):
    """
    Dummy admin entry to expose 'Error Lookup' in the sidebar.
    """
    change_list_template = "admin/error_lookup_link.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

