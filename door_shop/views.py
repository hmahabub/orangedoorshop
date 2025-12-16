from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models 
def index(request):
    """Main landing page"""
    return render(request, 'index.html')

@login_required
def dashboard(request):
    """Main dashboard after login"""
    from inventory.models import Product, Supplier, Customer
    from pos.models import Sale
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Calculate statistics
    total_products = Product.objects.count()
    total_suppliers = Supplier.objects.count()
    total_customers = Customer.objects.count()
    
    # Today's sales
    today = timezone.now().date()
    today_sales = Sale.objects.filter(sale_date__date=today)
    today_total = today_sales.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    today_count = today_sales.count()
    
    # Low stock alerts
    low_stock_products = Product.objects.filter(
        track_stock=True,
        current_stock__lte=models.F('min_stock_level')
    )[:5]
    
    # Recent sales
    recent_sales = Sale.objects.select_related('customer').order_by('-sale_date')[:5]
    
    context = {
        'total_products': total_products,
        'total_suppliers': total_suppliers,
        'total_customers': total_customers,
        'today_total': today_total,
        'today_count': today_count,
        'low_stock_products': low_stock_products,
        'recent_sales': recent_sales,
    }
    
    return render(request, 'dashboard.html', context)