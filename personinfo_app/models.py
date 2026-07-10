from django.db import models
from authenticate_app.models import Organization, Branch


# ==========================================================
# SUPPLIER MODEL
# ==========================================================
class Supplier(models.Model):
    code     = models.CharField(max_length=20)
    name     = models.CharField(max_length=100)
    mobile   = models.CharField(max_length=15)
    address  = models.TextField(blank=True, null=True)
    email    = models.EmailField(blank=True, null=True)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch       = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at   = models.DateTimeField(auto_now_add=True)   # set once at creation
    updated_at   = models.DateTimeField(auto_now=True)       # refreshes on every update

    created_by   = models.ForeignKey(
        'authenticate_app.User',
        on_delete=models.SET_NULL,
        related_name="supplier_created",
        null=True,
        blank=True
    )
    updated_by   = models.ForeignKey(
        'authenticate_app.User',
        on_delete=models.SET_NULL,
        related_name="supplier_updated",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        unique_together = [
            ('organization', 'code'),
            ('organization', 'mobile'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} (Supplier)"


# ==========================================================
# CUSTOMER MODEL
# ==========================================================
class Customer(models.Model):
    code     = models.CharField(max_length=20)
    name     = models.CharField(max_length=100)
    mobile   = models.CharField(max_length=15)
    address  = models.TextField(blank=True, null=True)
    email    = models.EmailField(blank=True, null=True)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch       = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at   = models.DateTimeField(auto_now_add=True)   # set once at creation
    updated_at   = models.DateTimeField(auto_now=True)       # refreshes on every update

    created_by   = models.ForeignKey(
        'authenticate_app.User',
        on_delete=models.SET_NULL,
        related_name="customer_created",
        null=True,
        blank=True
    )
    updated_by   = models.ForeignKey(
        'authenticate_app.User',
        on_delete=models.SET_NULL,
        related_name="customer_updated",
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['name']
        unique_together = [
            ('organization', 'code'),
            ('organization', 'mobile'),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} (Customer)"
