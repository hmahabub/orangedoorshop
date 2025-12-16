from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('stock-valuation/', views.stock_valuation_report, name='stock_valuation_report'),
    path('profit-calculation/', views.profit_calculation_report, name='profit_calculation_report'),
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('sales/', views.sales_report, name='sales_report'),
    path('customers/', views.customer_report, name='customer_report'),
    path('suppliers/', views.supplier_report, name='supplier_report'),
]