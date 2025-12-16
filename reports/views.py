from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from inventory.models import Product, PurchaseOrder, Customer, Supplier
from pos.models import Sale, DailySummary, SaleItem
from django.db.models import F

@login_required
def reports_dashboard(request):
    return render(request, 'reports/dashboard.html')

@login_required
def stock_valuation_report(request):
    products = Product.objects.filter(track_stock=True).select_related('category')
    
    # Calculate totals
    total_valuation = sum(product.stock_value for product in products)
    total_products = products.count()
    low_stock_count = products.filter(current_stock__lte=models.F('min_stock_level')).count()
    
    # Filter by category if provided
    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category_id=category_filter)
    
    context = {
        'products': products,
        'total_valuation': total_valuation,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'reports/stock_valuation.html', context)

@login_required
def profit_calculation_report(request):
    # Default to last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get date range from request
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    sales = Sale.objects.filter(sale_date__date__range=[start_date, end_date])
    
    # Calculate totals
    total_sales = sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    total_discount = sales.aggregate(total=Sum('discount_amount'))['total'] or Decimal('0')
    
    # Calculate cost and profit
    total_cost = Decimal('0')
    total_profit = Decimal('0')
    
    for sale in sales:
        for item in sale.items.all():
            cost = item.product.cost_price * item.quantity
            total_cost += cost
            total_profit += (item.total_price - cost)
    
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else Decimal('0')
    
    # Sales by payment method
    payment_methods = {
        'cash': sales.filter(payment_method='cash').aggregate(total=Sum('grand_total'))['total'] or Decimal('0'),
        'card': sales.filter(payment_method='card').aggregate(total=Sum('grand_total'))['total'] or Decimal('0'),
        'mobile': sales.filter(payment_method='mobile').aggregate(total=Sum('grand_total'))['total'] or Decimal('0'),
        'due': sales.filter(payment_method='due').aggregate(total=Sum('grand_total'))['total'] or Decimal('0'),
    }
    
    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'profit_margin': profit_margin,
        'total_discount': total_discount,
        'payment_methods': payment_methods,
    }
    return render(request, 'reports/profit_calculation.html', context)

@login_required
def low_stock_report(request):
    low_stock_products = Product.objects.filter(
        track_stock=True,
        current_stock__lte=F('min_stock_level')
    ).select_related('category')
    
    # Calculate restock needs
    for product in low_stock_products:
        product.restock_needed = max(0, product.min_stock_level - product.current_stock)
        product.restock_value = product.restock_needed * product.cost_price
    
    total_restock_value = sum(product.restock_value for product in low_stock_products)
    
    context = {
        'products': low_stock_products,
        'total_restock_value': total_restock_value,
    }
    return render(request, 'reports/low_stock.html', context)

@login_required
def sales_report(request):
    # Default to last 7 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    sales = Sale.objects.filter(sale_date__date__range=[start_date, end_date]).select_related('customer')
    
    # Daily breakdown
    daily_summaries = []
    current_date = start_date
    while current_date <= end_date:
        daily_sales = sales.filter(sale_date__date=current_date)
        daily_total = daily_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
        daily_count = daily_sales.count()
        
        daily_summaries.append({
            'date': current_date,
            'total_sales': daily_total,
            'sale_count': daily_count,
        })
        current_date += timedelta(days=1)
    
    # Top selling products
    top_products = SaleItem.objects.filter(
        sale__sale_date__date__range=[start_date, end_date]
    ).values(
        'product__name', 'product__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:10]
    
    # Sales statistics
    total_sales_amount = sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
    total_transactions = sales.count()
    avg_sale_value = total_sales_amount / total_transactions if total_transactions > 0 else Decimal('0')
    
    context = {
        'sales': sales,
        'daily_summaries': daily_summaries,
        'top_products': top_products,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales_amount,
        'total_transactions': total_transactions,
        'avg_sale_value': avg_sale_value,
    }
    return render(request, 'reports/sales_report.html', context)

@login_required
def customer_report(request):
    customers = Customer.objects.all()
    
    # Add sales data to customers
    for customer in customers:
        customer_sales = Sale.objects.filter(customer=customer)
        customer.sales_count = customer_sales.count()
        customer.total_spent = customer_sales.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')
        customer.last_purchase = customer_sales.order_by('-sale_date').first()
    
    # Top customers by spending
    top_customers = sorted(
        [c for c in customers if c.total_spent > 0],
        key=lambda x: x.total_spent,
        reverse=True
    )[:10]
    
    # Customer statistics
    total_customers = customers.count()
    active_customers = len([c for c in customers if c.sales_count > 0])
    total_revenue = sum(customer.total_spent for customer in customers)
    avg_spent = total_revenue / active_customers if active_customers > 0 else Decimal('0')
    
    context = {
        'customers': customers,
        'top_customers': top_customers,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_revenue': total_revenue,
        'avg_spent': avg_spent,
    }
    return render(request, 'reports/customer_report.html', context)

@login_required
def supplier_report(request):
    suppliers = Supplier.objects.all()
    
    # Add purchase data to suppliers
    for supplier in suppliers:
        supplier_purchases = PurchaseOrder.objects.filter(supplier=supplier)
        supplier.purchase_count = supplier_purchases.count()
        supplier.total_purchases = supplier_purchases.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        supplier.last_purchase = supplier_purchases.order_by('-order_date').first()
    
    # Supplier statistics
    total_suppliers = suppliers.count()
    active_suppliers = len([s for s in suppliers if s.purchase_count > 0])
    total_purchase_value = sum(supplier.total_purchases for supplier in suppliers)
    
    context = {
        'suppliers': suppliers,
        'total_suppliers': total_suppliers,
        'active_suppliers': active_suppliers,
        'total_purchase_value': total_purchase_value,
    }
    return render(request, 'reports/supplier_report.html', context)