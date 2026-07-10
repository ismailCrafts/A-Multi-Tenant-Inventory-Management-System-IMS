from django.db import models
from decimal import Decimal
from authenticate_app.models import Organization, Branch


# ==========================================================
# OPENING STOCK MODEL
# ==========================================================
class OpeningStock(models.Model):
    """
    Represents the initial stock for a product.
    """

    # Tenant linkage
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    # Product taxonomy
    date = models.DateField()
    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    # Stock metrics
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="openingstock_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="openingstock_updated")

    class Meta:
        verbose_name = "Opening Stock"
        verbose_name_plural = "Opening Stock Entries"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"


# ==========================================================
# PURCHASE MODEL
# ==========================================================
class Purchase(models.Model):
    """
    Represents a supplier purchase.
    """

    date = models.DateField(auto_now_add=True)
    purchase_code = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)

    supplier_name = models.CharField(max_length=100)
    supplier_mobile = models.CharField(max_length=15, blank=True, null=True)
    supplier_address = models.TextField(blank=True, null=True)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchase_updated")

    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-date']

    def __str__(self):
        return f"{self.purchase_code} - {self.supplier_name}"


class PurchaseItem(models.Model):
    """
    Line item within a purchase.
    """

    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchaseitem_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchaseitem_updated")

    class Meta:
        verbose_name = "Purchase Item"
        verbose_name_plural = "Purchase Items"
        constraints = [
            models.UniqueConstraint(fields=['purchase', 'product'], name='unique_product_per_purchase'),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.purchase.purchase_code})"


# ==========================================================
# SALE MODEL
# ==========================================================
class Sale(models.Model):
    """
    Represents a customer sale.
    """

    date = models.DateField(auto_now_add=True)
    sale_code = models.CharField(max_length=50, unique=True)
    narration = models.TextField(blank=True, null=True)

    customer_name = models.CharField(max_length=100)
    customer_mobile = models.CharField(max_length=15, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="sale_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="sale_updated")

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-date']

    def __str__(self):
        return f"{self.sale_code} - {self.customer_name}"


class SaleItem(models.Model):
    """
    Line item within a sale.
    """

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="saleitem_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="saleitem_updated")

    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"
        constraints = [
            models.UniqueConstraint(fields=['sale', 'product'], name='unique_product_per_sale'),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.sale.sale_code})"


# ==========================================================
# PURCHASE RETURN MODEL
# ==========================================================
class PurchaseReturn(models.Model):
    """
    Represents a return to the supplier.
    """

    date = models.DateField(auto_now_add=True)
    return_code = models.CharField(max_length=50, unique=True)
    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True)

    supplier_name = models.CharField(max_length=100)
    supplier_mobile = models.CharField(max_length=15, blank=True, null=True)
    supplier_address = models.TextField(blank=True, null=True)
    narration = models.TextField(blank=True, null=True)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchasereturn_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchasereturn_updated")

    class Meta:
        verbose_name = "Purchase Return"
        verbose_name_plural = "Purchase Returns"
        ordering = ['-date']

    def __str__(self):
        return f"{self.return_code} - {self.supplier_name}"


class PurchaseReturnItem(models.Model):
    """
    Line item within a purchase return.
    """

    purchase_return = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='items')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchasereturnitem_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="purchasereturnitem_updated")

    class Meta:
        verbose_name = "Purchase Return Item"
        verbose_name_plural = "Purchase Return Items"
        constraints = [
            models.UniqueConstraint(fields=['purchase_return', 'product'], name='unique_product_per_purchase_return'),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.purchase_return.return_code})"


# ==========================================================
# SALE RETURN MODEL
# ==========================================================
class SaleReturn(models.Model):
    """
    Represents a return from the customer.
    """

    date = models.DateField(auto_now_add=True)
    return_code = models.CharField(max_length=50, unique=True)
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True)

    customer_name = models.CharField(max_length=100)
    customer_mobile = models.CharField(max_length=15, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    narration = models.TextField(blank=True, null=True)

    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    refund_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    due_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="salereturn_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="salereturn_updated")

    class Meta:
        verbose_name = "Sale Return"
        verbose_name_plural = "Sale Returns"
        ordering = ['-date']

    def __str__(self):
        return f"{self.return_code} - {self.customer_name}"


class SaleReturnItem(models.Model):
    """
    Line item within a sale return.
    """

    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name='items')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="salereturnitem_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="salereturnitem_updated")

    class Meta:
        verbose_name = "Sale Return Item"
        verbose_name_plural = "Sale Return Items"
        constraints = [
            models.UniqueConstraint(fields=['sale_return', 'product'], name='unique_product_per_sale_return'),
        ]

    def __str__(self):
        return f"{self.product.name} x {self.quantity} ({self.sale_return.return_code})"


# ==========================================================
# PRODUCT REJECT MODEL
# ==========================================================
class ProductReject(models.Model):
    """
    Represents rejected products on the supplier side.
    """

    date = models.DateField(auto_now_add=True)
    reject_code = models.CharField(max_length=50, unique=True)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)

    category = models.ForeignKey('product_app.Category', on_delete=models.CASCADE)
    product_group = models.ForeignKey('product_app.ProductGroup', on_delete=models.CASCADE)
    brand = models.ForeignKey('product_app.Brand', on_delete=models.CASCADE)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE)

    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    REJECT_REASONS = [
        ('damaged', 'Damaged'),
        ('expired', 'Expired'),
        ('defective', 'Defective'),
        ('contaminated', 'Contaminated'),
        ('other', 'Other'),
    ]
    reason = models.CharField(max_length=20, choices=REJECT_REASONS, default='damaged')

    purchase = models.ForeignKey(Purchase, on_delete=models.SET_NULL, null=True, blank=True, help_text="Optional: link to original purchase")
    narration = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="productreject_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="productreject_updated")

    class Meta:
        verbose_name = "Product Reject"
        verbose_name_plural = "Product Reject Entries"
        ordering = ['-date']

    def __str__(self):
        return f"{self.reject_code} - {self.product.name} ({self.reason})"


# ==========================================================
# STOCK RESERVATION MODEL
# ==========================================================
class StockReservation(models.Model):
    """
    Temporary stock hold while a user is filling out a sale/form.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, blank=True, null=True)
    product = models.ForeignKey('product_app.Product', on_delete=models.CASCADE, related_name='reservations')

    session_key = models.CharField(max_length=100, help_text="User's session key — identifies who holds this reservation")
    reserved_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(help_text="Reservation auto-expires after this time")

    created_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="stockreservation_created")
    updated_by = models.ForeignKey('authenticate_app.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="stockreservation_updated")

    class Meta:
        verbose_name = "Stock Reservation"
        verbose_name_plural = "Stock Reservations"
        indexes = [
            models.Index(fields=['product', 'organization', 'branch'], name='reservation_product_org_idx'),
            models.Index(fields=['session_key'], name='reservation_session_idx'),
            models.Index(fields=['expires_at'], name='reservation_expires_idx'),
            models.Index(fields=['organization', 'branch', 'expires_at'], name='reservation_cleanup_idx'),
            models.Index(fields=['product', 'session_key', 'expires_at'], name='reservation_prod_sess_idx'),
        ]

    def __str__(self):
        return f"{self.product.name} reserved {self.reserved_quantity} (session {self.session_key})"
