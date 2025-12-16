from django.db import models
from django.contrib.auth.models import User
from inventory.models import Product, Customer
from decimal import Decimal

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Banking'),
        ('due', 'Customer Due'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_person = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    receipt_printed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.grand_total = self.total_amount - self.discount_amount + self.tax_amount
        if self.payment_method != 'due':
            self.change_given = max(Decimal('0.00'), self.payment_received - self.grand_total)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sale #{self.id} - {self.sale_date.strftime('%Y-%m-%d %H:%M')}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update sale total
        self.sale.total_amount = sum(item.total_price for item in self.sale.items.all())
        self.sale.save()
        
        # Update stock
        if self.product.track_stock:
            self.product.current_stock -= self.quantity
            self.product.save()

class Payment(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=Sale.PAYMENT_METHODS)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

class DailySummary(models.Model):
    date = models.DateField(unique=True)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_card = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_mobile = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def update_totals(self):
        from django.db.models import Sum
        sales = Sale.objects.filter(sale_date__date=self.date)
        
        self.total_sales = sales.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        self.total_cash = sales.filter(payment_method='cash').aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        self.total_card = sales.filter(payment_method='card').aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        self.total_mobile = sales.filter(payment_method='mobile').aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        self.total_due = sales.filter(payment_method='due').aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        self.total_discount = sales.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
        
        # Calculate profit (simplified)
        profit = 0
        for sale in sales:
            for item in sale.items.all():
                cost = item.product.cost_price * item.quantity
                profit += (item.total_price - cost)
        self.total_profit = profit
        
        self.save()