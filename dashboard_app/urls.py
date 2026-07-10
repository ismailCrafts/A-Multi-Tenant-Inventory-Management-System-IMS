from django.urls import path
from . import views
urlpatterns = [
    path("error-lookup/", views.error_lookup, name="error_lookup"),
]
