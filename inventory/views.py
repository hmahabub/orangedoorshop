from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
from .models import Product, Category, Supplier, Customer, PurchaseOrder, PurchaseItem, StockAdjustment
from .forms import ProductForm, SupplierForm, CustomerForm, PurchaseOrderForm, PurchaseItemForm, StockAdjustmentForm
from django.db import models

@login_required
def product_list(request):
    products = Product.objects.all().select_related('category')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(material__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by product type
    product_type = request.GET.get('product_type')
    if product_type:
        products = products.filter(product_type=product_type)
    
    categories = Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'product_types': Product.PRODUCT_TYPES,
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'inventory/product_detail.html', {'product': product})

@login_required
def product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Add New Product'
    })

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'inventory/product_form.html', {
        'form': form,
        'title': 'Edit Product'
    })

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')
    
    return render(request, 'inventory/product_confirm_delete.html', {'product': product})

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    
    query = request.GET.get('q')
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) |
            Q(contact_person__icontains=query) |
            Q(phone__icontains=query)
        )
    
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_add(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" added successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'inventory/supplier_form.html', {
        'form': form,
        'title': 'Add New Supplier'
    })

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully!')
            return redirect('supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'inventory/supplier_form.html', {
        'form': form,
        'title': 'Edit Supplier'
    })

# Add these imports at the top if not already present
from django.db.models import Count, Sum, Q
from pos.models import Sale

# Add these customer views to your existing views
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('-created_at')
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(address__icontains=query)
        )
    
    # Calculate customer statistics
    for customer in customers:
        customer_sales = Sale.objects.filter(customer=customer)
        customer.sales_count = customer_sales.count()
        customer.total_spent = customer_sales.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        customer.last_purchase = customer_sales.order_by('-sale_date').first()
    
    # Summary statistics
    total_customers = customers.count()
    active_customers = len([c for c in customers if c.sales_count > 0])
    total_revenue = sum(customer.total_spent for customer in customers)
    avg_spent = total_revenue / active_customers if active_customers > 0 else 0
    
    context = {
        'customers': customers,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'total_revenue': total_revenue,
        'avg_spent': avg_spent,
    }
    return render(request, 'inventory/customer_list.html', context)

@login_required
def customer_add(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" added successfully!')
            return redirect('customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm()
    
    return render(request, 'inventory/customer_form.html', {
        'form': form,
        'title': 'Add New Customer'
    })

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.name}" updated successfully!')
            return redirect('customer_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomerForm(instance=customer)
    
    return render(request, 'inventory/customer_form.html', {
        'form': form,
        'title': f'Edit Customer: {customer.name}'
    })

@login_required
def customer_sales(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = Sale.objects.filter(customer=customer).select_related('sale_person').order_by('-sale_date')
    
    # Sales statistics
    total_sales = sales.count()
    total_amount = sales.aggregate(Sum('grand_total'))['grand_total__sum'] or 0
    total_discount = sales.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0
    
    # Payment method breakdown
    payment_methods = sales.values('payment_method').annotate(
        count=Count('id'),
        total=Sum('grand_total')
    )
    
    context = {
        'customer': customer,
        'sales': sales,
        'total_sales': total_sales,
        'total_amount': total_amount,
        'total_discount': total_discount,
        'payment_methods': payment_methods,
    }
    return render(request, 'inventory/customer_sales.html', context)

# Add these imports at the top if not already present
from django.db.models import Count, Sum, Q
from django.http import HttpResponseRedirect

# Add these purchase views to your existing views
@login_required
def purchase_list(request):
    purchases = PurchaseOrder.objects.all().select_related('supplier').order_by('-order_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        purchases = purchases.filter(status=status_filter)
    
    # Calculate statistics
    total_purchases = purchases.count()
    pending_count = purchases.filter(status='pending').count()
    received_count = purchases.filter(status='received').count()
    total_amount = purchases.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    context = {
        'purchases': purchases,
        'status_choices': PurchaseOrder._meta.get_field('status').choices,
        'total_purchases': total_purchases,
        'pending_count': pending_count,
        'received_count': received_count,
        'total_amount': total_amount,
    }
    return render(request, 'inventory/purchase_list.html', context)

@login_required
def purchase_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            messages.success(request, f'Purchase order #{purchase.id} created successfully!')
            return redirect('purchase_detail', pk=purchase.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderForm()
    
    return render(request, 'inventory/purchase_form.html', {
        'form': form,
        'title': 'Create Purchase Order'
    })

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    items = purchase.items.all().select_related('product')
    
    if request.method == 'POST' and purchase.status == 'pending':
        item_form = PurchaseItemForm(request.POST)
        if item_form.is_valid():
            item = item_form.save(commit=False)
            item.purchase_order = purchase
            item.save()
            purchase.update_total()
            messages.success(request, 'Item added to purchase order!')
            return redirect('purchase_detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        item_form = PurchaseItemForm()
    
    context = {
        'purchase': purchase,
        'items': items,
        'item_form': item_form,
    }
    return render(request, 'inventory/purchase_detail.html', context)

@login_required
def purchase_receive(request, pk):
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    
    if request.method == 'POST':
        purchase.status = 'received'
        purchase.save()
        
        # Update product stocks and costs
        for item in purchase.items.all():
            if item.product.track_stock:
                item.product.current_stock += item.quantity
                item.product.cost_price = item.unit_cost
                item.product.save()
        
        messages.success(request, f'Purchase order #{purchase.id} marked as received! Stock levels updated.')
        return redirect('purchase_detail', pk=pk)
    
    return render(request, 'inventory/purchase_receive_confirm.html', {'purchase': purchase})

@login_required
def purchase_item_delete(request, pk):
    item = get_object_or_404(PurchaseItem, pk=pk)
    purchase = item.purchase_order
    
    if request.method == 'POST' and purchase.status == 'pending':
        item.delete()
        purchase.update_total()
        messages.success(request, 'Item removed from purchase order!')
    
    return redirect('purchase_detail', pk=purchase.pk)



# Add these stock adjustment views to your existing views
@login_required
def stock_adjustment_list(request):
    adjustments = StockAdjustment.objects.all().select_related('product', 'created_by').order_by('-created_at')
    
    # Calculate statistics
    total_adjustments = adjustments.count()
    stock_in_count = adjustments.filter(adjustment_type='in').count()
    stock_out_count = adjustments.filter(adjustment_type='out').count()
    adjustment_count = adjustments.filter(adjustment_type='adjust').count()
    
    # Calculate total quantities
    total_stock_in = adjustments.filter(adjustment_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_stock_out = adjustments.filter(adjustment_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
    net_change = total_stock_in - total_stock_out
    
    context = {
        'adjustments': adjustments,
        'total_adjustments': total_adjustments,
        'stock_in_count': stock_in_count,
        'stock_out_count': stock_out_count,
        'adjustment_count': adjustment_count,
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,
        'net_change': net_change,
    }
    return render(request, 'inventory/stock_adjustment_list.html', context)

@login_required
def stock_adjustment_create(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.created_by = request.user
            
            # Handle different adjustment types
            product = adjustment.product
            if product.track_stock:
                if adjustment.adjustment_type == 'in':
                    # Add stock
                    pass
                elif adjustment.adjustment_type == 'out':
                    # Remove stock (ensure we don't go negative)
                    if adjustment.quantity <= product.current_stock:
                        pass
                    else:
                        messages.error(request, f'Cannot remove {adjustment.quantity} units. Only {product.current_stock} units available.')
                        return render(request, 'inventory/stock_adjustment_form.html', {
                            'form': form,
                            'title': 'Stock Adjustment'
                        })
                elif adjustment.adjustment_type == 'adjust':
                    # Direct adjustment - you might want to handle this differently
                    # For now, we'll treat it as setting to a specific value
                    pass
                
                product.save()
            
            adjustment.save()
            messages.success(request, f'Stock adjustment for {product.name} completed successfully!')
            return redirect('stock_adjustment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StockAdjustmentForm()
    
    return render(request, 'inventory/stock_adjustment_form.html', {
        'form': form,
        'title': 'Stock Adjustment'
    })

# API view for product stock information
@login_required
def api_product_stock_info(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'current_stock': float(product.current_stock),
        'min_stock_level': float(product.min_stock_level),
        'track_stock': product.track_stock,
        'category': product.category.name,
    })

@login_required
def dashboard(request):
    # Basic dashboard statistics
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(
        track_stock=True,
        current_stock__lte=models.F('min_stock_level')
    ).count()
    
    total_suppliers = Supplier.objects.count()
    total_customers = Customer.objects.count()
    
    # Recent purchases
    recent_purchases = PurchaseOrder.objects.select_related('supplier').order_by('-order_date')[:5]
    
    # Low stock alerts
    low_stock_alerts = Product.objects.filter(
        track_stock=True,
        current_stock__lte=models.F('min_stock_level')
    )[:10]
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_suppliers': total_suppliers,
        'total_customers': total_customers,
        'recent_purchases': recent_purchases,
        'low_stock_alerts': low_stock_alerts,
    }
    
    return render(request, 'inventory/dashboard.html', context)

# API views for AJAX calls
@login_required
def api_product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)[:10]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'selling_price': str(product.selling_price),
            'current_stock': str(product.current_stock),
            'track_stock': product.track_stock
        })
    
    return JsonResponse(results, safe=False)