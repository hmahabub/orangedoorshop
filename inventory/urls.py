from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='inventory_dashboard'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Suppliers
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    
    # Customers
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/sales/', views.customer_sales, name='customer_sales'),
    
    # Purchases
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/receive/', views.purchase_receive, name='purchase_receive'),
    path('purchase-item/<int:pk>/delete/', views.purchase_item_delete, name='purchase_item_delete'),
    
     # Stock Adjustments
    path('stock-adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
    path('stock-adjustments/create/', views.stock_adjustment_create, name='stock_adjustment_create'),
    
    # API endpoints
    path('api/product/<int:product_id>/stock-info/', views.api_product_stock_info, name='api_product_stock_info'),
    
    # API endpoints
    path('api/product-search/', views.api_product_search, name='api_product_search'),
]