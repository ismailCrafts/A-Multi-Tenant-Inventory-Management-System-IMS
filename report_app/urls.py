from django.urls import path
from . import views


# ==========================================================
# REPORT APP URLS
# ==========================================================
urlpatterns = [
    # Step 1: Report form (entry point for selecting topic/date/org/branch)
    path("form/", views.report_form, name="report_form"),

    # Step 2: Preview report in browser (renders HTML template with data)
    path("preview/", views.preview_report, name="preview_report"),

    # Step 3: Download report as PDF (WeasyPrint output)
    path("download/", views.download_report, name="download_report"),
]
