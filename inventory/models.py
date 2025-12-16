from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class Supplier(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20,unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Make unique and allow null
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phone'],
                name='unique_phone_when_not_null',
                condition=models.Q(phone__isnull=False)
            )
        ]

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    PRODUCT_TYPES = [
        ('ready_made', 'Ready-made Door'),
        ('custom', 'Custom Door'),
        ('frame', 'Door Frame'),
        ('accessory', 'Accessory'),
        ('material', 'Raw Material'),
        ('service', 'Service/Labour'),
    ]

    # Existing fields
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    description = models.TextField(blank=True)

    # New: Supplier & item identification
    supplier_name = models.ForeignKey(Supplier, on_delete=models.CASCADE)   # National / ND / GD / PD / etc.
    supplier_item_code = models.CharField(max_length=100, blank=True)  # e.g. 015.112.1149, ND-101

    # Door specs
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    thickness = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    material = models.CharField(max_length=100, blank=True)

    # New: door technical attributes
    opening_side = models.CharField(max_length=10, blank=True, null=True)  # Right/Left/Both
    accessories = models.CharField(max_length=200, blank=True)  # Chitkini, Hasbolt, Mini Hasbolt
        
    # Pricing
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    # Stock
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    track_stock = models.BooleanField(default=True)

    # Extra (optional)
    remarks = models.CharField(max_length=255, blank=True)  # Frame size, colour, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.product_type in ['ready_made', 'custom', 'frame']:
            size = f"{self.width}x{self.height}x{self.thickness}"
            return f"{self.name} ({size})"
        return self.name

    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.selling_price - self.cost_price) / self.cost_price) * 100
        return 0

    @property
    def stock_value(self):
        return self.current_stock * self.cost_price


class PurchaseOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def update_total(self):
        self.total_amount = sum(item.total_price for item in self.items.all())
        self.save()

class PurchaseItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
        
        # Update product cost price if this is the latest purchase
        if self.purchase_order.status == 'received':
            self.product.cost_price = self.unit_cost
            if self.product.track_stock:
                self.product.current_stock += self.quantity
            self.product.save()

class StockAdjustment(models.Model):
    ADJUSTMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjust', 'Adjustment'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_adjustment_type_display()} - {self.product.name} - {self.quantity}"

    def save(self, *args, **kwargs):
        # First save the adjustment
        super().save(*args, **kwargs)
        
        # Then update product stock if tracking is enabled
        if self.product.track_stock:
            if self.adjustment_type == 'in':
                self.product.current_stock += self.quantity
            elif self.adjustment_type == 'out':
                # Ensure we don't go negative (should be validated in form)
                if self.quantity <= self.product.current_stock:
                    self.product.current_stock -= self.quantity
            # For 'adjust' type, you might want different logic
            self.product.save()