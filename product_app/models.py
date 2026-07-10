from django.db import models
from authenticate_app.models import Organization, Branch


# ==========================================================
# CATEGORY MODEL
# ==========================================================
class Category(models.Model):
    """
    Represents a product category scoped to an organization/branch.
    Steps:
    1. Define core fields (name, description).
    2. Link to Organization + optional Branch.
    3. Track creation + update timestamps.
    4. Track created_by and updated_by.
    5. Enforce uniqueness per organization.
    6. String representation for admin/debug.
    """

    # Step 1: Core fields
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    # Step 2: Tenant linkage
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    # Step 3: Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Step 4: Audit users
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="category_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="category_updated")

    class Meta:
        # Step 5: Unique per organization
        unique_together = ('organization', 'name')
        ordering = ['name']

    # Step 6: String representation
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ==========================================================
# BRAND MODEL
# ==========================================================
class Brand(models.Model):
    """
    Represents a product brand scoped to an organization/branch.
    Steps:
    1. Define core fields (name, brand_code, description).
    2. Link to Organization + optional Branch.
    3. Track creation + update timestamps.
    4. Track created_by and updated_by.
    5. Enforce uniqueness per organization.
    6. String representation for admin/debug.
    """

    # Step 1: Core fields
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    # Step 2: Tenant linkage
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    # Step 3: Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Step 4: Audit users
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="brand_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="brand_updated")

    class Meta:
        # Step 5: Unique per organization
        unique_together = ('organization', 'code')
        ordering = ['name']

    # Step 6: String representation
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ==========================================================
# PRODUCT GROUP MODEL
# ==========================================================
class ProductGroup(models.Model):
    """
    Represents a grouping of products under a category and brand.
    Scoped to an organization/branch.
    Steps:
    1. Define core fields (name, code, description).
    2. Link to Category, Brand, Organization, Branch.
    3. Track creation + update timestamps.
    4. Track created_by and updated_by.
    5. Enforce uniqueness per organization.
    6. String representation for admin/debug.
    """

    # Step 1: Core fields
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    # Step 2: Foreign keys
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    # Step 3: Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Step 4: Audit users
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="productgroup_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="productgroup_updated")

    class Meta:
        # Step 5: Unique per organization
        unique_together = ('organization', 'code')
        ordering = ['name']

    # Step 6: String representation
    def __str__(self):
        return f"{self.name} ({self.organization.name})"


# ==========================================================
# PRODUCT MODEL
# ==========================================================
class Product(models.Model):
    """
    Represents a product tied to category, brand, and product group.
    Scoped to an organization/branch.
    Steps:
    1. Define core fields (name, code, description).
    2. Add barcode fields.
    3. Link to Category, Brand, ProductGroup, Organization, Branch.
    4. Add low stock threshold.
    5. Track creation + update timestamps.
    6. Track created_by and updated_by.
    7. Enforce uniqueness per organization.
    8. String representation for admin/debug.
    """

    # Step 1: Core fields
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Step 2: Barcode fields
    barcode_number = models.CharField(max_length=50, blank=True, null=True)
    barcode_image = models.ImageField(upload_to='barcodes/', blank=True, null=True)

    # Step 3: Foreign keys
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    product_group = models.ForeignKey(ProductGroup, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    # Step 4: Low stock threshold
    low_stock_threshold = models.PositiveIntegerField(
        default=0,
        help_text="Minimum stock level before alert/notification"
    )

    # Step 5: Audit timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Step 6: Audit users
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="product_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="product_updated")

    class Meta:
        # Step 7: Unique per organization
        unique_together = ('organization', 'barcode_number')
        ordering = ['name']

    # Step 8: String representation
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
