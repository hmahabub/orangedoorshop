from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Sale, SaleItem, DailySummary
from .forms import SaleForm, SaleItemForm
from inventory.models import Product, Customer
import json
from decimal import Decimal
from inventory.forms import CustomerForm

@login_required
def get_product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'selling_price': str(product.selling_price),
        'current_stock': str(product.current_stock),
        'track_stock': product.track_stock,
        'min_stock_level': str(product.min_stock_level)
    })

@login_required
@csrf_exempt
@transaction.atomic
def create_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate stock before creating sale
            for item_data in data.get('items', []):
                product = Product.objects.get(id=item_data['product_id'])
                quantity = Decimal(item_data['quantity'])
                
                if product.track_stock and quantity > product.current_stock:
                    return JsonResponse({
                        'success': False,
                        'error': f'Not enough stock for {product.name}. Available: {product.current_stock}'
                    })
            
            # Create sale
            sale = Sale(
                customer_id=data.get('customer_id'),
                discount_amount=Decimal(data.get('discount_amount', 0)),
                payment_method=data.get('payment_method', 'cash'),
                payment_received=Decimal(data.get('payment_received', 0)),
                sale_person=request.user,
                notes=data.get('notes', '')
            )
            sale.save()
            
            # Add sale items and update stock
            for item_data in data.get('items', []):
                product = Product.objects.get(id=item_data['product_id'])
                quantity = Decimal(item_data['quantity'])
                
                sale_item = SaleItem(
                    sale=sale,
                    product=product,
                    quantity=quantity,
                    unit_price=Decimal(item_data['unit_price'])
                )
                sale_item.save()
                
                # Update product stock
                if product.track_stock:
                    product.current_stock -= quantity
                    product.save()
            
            # Update daily summary
            date = sale.sale_date.date()
            daily_summary, created = DailySummary.objects.get_or_create(date=date)
            daily_summary.update_totals()
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'grand_total': str(sale.grand_total),
                'change_given': str(sale.change_given)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def search_or_create_customer(request):
    """Search customer by mobile number or create new one"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone = data.get('phone', '').strip()
            name = data.get('name', '').strip()
            
            if not phone:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number is required'
                })
            
            # Clean phone number
            phone = phone.replace(' ', '').replace('-', '').replace('+', '')
            
            # Search for existing customer
            try:
                customer = Customer.objects.get(phone=phone)
                return JsonResponse({
                    'success': True,
                    'customer': {
                        'id': customer.id,
                        'name': customer.name,
                        'phone': customer.phone,
                        'email': customer.email or '',
                        'address': customer.address or ''
                    },
                    'exists': True
                })
            except Customer.DoesNotExist:
                # Create new customer
                if not name:
                    name = f"Customer {phone}"  # Default name
                
                customer = Customer.objects.create(
                    name=name,
                    phone=phone,
                    email=data.get('email', ''),
                    address=data.get('address', '')
                )
                
                return JsonResponse({
                    'success': True,
                    'customer': {
                        'id': customer.id,
                        'name': customer.name,
                        'phone': customer.phone,
                        'email': customer.email or '',
                        'address': customer.address or ''
                    },
                    'exists': False,
                    'message': 'New customer created successfully'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_customer_by_phone(request, phone):
    """Get customer details by phone number"""
    try:
        # Clean phone number
        phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        
        customer = Customer.objects.get(phone=phone)
        return JsonResponse({
            'success': True,
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email or '',
                'address': customer.address or ''
            }
        })
    except Customer.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Customer not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def pos_dashboard(request):
    products = Product.objects.all()
    customers = Customer.objects.all()
    return render(request, 'pos/dashboard.html', {
        'products': products,
        'customers': customers
    })

@login_required
def get_product_details(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return JsonResponse({
        'id': product.id,
        'name': product.name,
        'selling_price': str(product.selling_price),
        'current_stock': str(product.current_stock),
        'track_stock': product.track_stock
    })

@login_required
@csrf_exempt
@transaction.atomic
def create_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create sale
            sale = Sale(
                customer_id=data.get('customer_id'),
                discount_amount=Decimal(data.get('discount_amount', 0)),
                payment_method=data.get('payment_method', 'cash'),
                payment_received=Decimal(data.get('payment_received', 0)),
                sale_person=request.user,
                notes=data.get('notes', '')
            )
            sale.save()
            
            # Add sale items
            for item_data in data.get('items', []):
                product = Product.objects.get(id=item_data['product_id'])
                sale_item = SaleItem(
                    sale=sale,
                    product=product,
                    quantity=Decimal(item_data['quantity']),
                    unit_price=Decimal(item_data['unit_price'])
                )
                sale_item.save()
            
            # Update daily summary
            date = sale.sale_date.date()
            daily_summary, created = DailySummary.objects.get_or_create(date=date)
            daily_summary.update_totals()
            
            return JsonResponse({
                'success': True,
                'sale_id': sale.id,
                'grand_total': str(sale.grand_total),
                'change_given': str(sale.change_given)
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def print_receipt(request, sale_id):
    sale = get_object_or_404(Sale, id=sale_id)
    sale.receipt_printed = True
    sale.save()
    
    return render(request, 'pos/receipt.html', {'sale': sale})

@login_required
def daily_sales_report(request):
    date = request.GET.get('date')
    if date:
        sales = Sale.objects.filter(sale_date__date=date)
        daily_summary, created = DailySummary.objects.get_or_create(date=date)
        if created:
            daily_summary.update_totals()
    else:
        sales = Sale.objects.all()[:50]
        daily_summary = None
    
    return render(request, 'pos/daily_sales.html', {
        'sales': sales,
        'daily_summary': daily_summary,
        'selected_date': date
    })